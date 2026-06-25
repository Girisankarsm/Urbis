"""Discover official municipal complaint emails via public web search."""

from __future__ import annotations

import asyncio
import logging
import re
from html import unescape
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.models import ClassificationResult
from app.services.authority_lookup import _classify_issue_type
from app.services.departments import ISSUE_KEYWORDS
from app.services.geocoding import GeoArea

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
DDG_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "Mozilla/5.0 (compatible; Urbis/1.0; civic-complaint-routing)"

BLOCKED_DOMAINS = frozenset(
    {
        "example.com",
        "demo.local",
        "mcmc-demo.gov",
        "test.com",
        "localhost",
        "sentry.io",
        "w3.org",
        "schema.org",
        "gccservices.in",
    }
)
BLOCKED_LOCALPARTS = frozenset({"noreply", "no-reply", "donotreply", "mailer-daemon"})

ISSUE_EMAIL_HINTS: dict[str, tuple[str, ...]] = {
    "garbage": ("waste", "sanitation", "swm", "garbage", "solid"),
    "pothole": ("road", "works", "engineering", "pwd"),
    "streetlight": ("electrical", "light", "street"),
    "water_leak": ("water", "jal", "metrowater", "supply"),
    "sewage": ("sewer", "drain", "sewage", "health"),
}


def _place_name(area: GeoArea) -> str:
    return (
        area.city
        or area.municipality
        or area.district
        or area.suburb
        or (area.display_name.split(",")[0] if area.display_name else "")
        or "municipality"
    ).strip()


def _is_blocked_email(email: str) -> bool:
    email_l = email.lower().strip()
    if "demo" in email_l or "fake" in email_l:
        return True
    local, _, domain = email_l.partition("@")
    if not domain or domain in BLOCKED_DOMAINS:
        return True
    if local in BLOCKED_LOCALPARTS:
        return True
    return False


def _extract_emails(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in EMAIL_RE.findall(text):
        email = match.lower().strip().rstrip(".,;)")
        if _is_blocked_email(email) or email in seen:
            continue
        seen.add(email)
        found.append(email)
    return found


def _score_email(email: str, area: GeoArea, issue_type: str) -> float:
    if _is_blocked_email(email):
        return -1.0

    email_l = email.lower()
    score = 0.0

    if email_l.endswith(".gov.in"):
        score += 6.0
    elif email_l.endswith("@chennaicorporation.gov.in"):
        score += 7.0
    elif email_l.endswith(".nic.in"):
        score += 5.0
    elif ".gov." in email_l or email_l.endswith(".gov"):
        score += 4.5
    elif any(token in email_l for token in ("officials.in", "mcgov", "corporation.org", "municipal")):
        score += 4.0
    elif any(token in email_l for token in ("municipal", "corporation", "nigam", "mcorp", "tmc", "bbmp", "bmc", "gcc", "ghmc")):
        score += 3.0
    elif email_l.endswith("@gmail.com") and issue_type == "garbage" and any(
        hint in email_l for hint in ("waste", "sanitation", "dump", "swm", "tmc")
    ):
        score += 3.5
    elif email_l.endswith("@gmail.com") and any(token in email_l for token in ("mc", "corp", "municipal", "tmc", "nigam")):
        score += 1.5
    elif email_l.endswith("@gmail.com"):
        score += 0.25
    else:
        score += 1.0

    place = _place_name(area).lower()
    if place and len(place) >= 4 and place[:4] in email_l:
        score += 1.0

    for hint in ISSUE_EMAIL_HINTS.get(issue_type, ()):
        if hint in email_l:
            score += 0.75

    if any(token in email_l for token in ("secretary", "complaint", "grievance", "mayor", "commissioner")):
        score += 1.0

    if email_l.endswith("@gmail.com") and issue_type == "garbage":
        if any(hint in email_l for hint in ("waste", "sanitation", "dump", "swm", "tmc")):
            score += 3.0

    return score


def _pick_best_email(
    emails: list[str],
    area: GeoArea,
    issue_type: str,
) -> str | None:
    if not emails:
        return None
    ranked = sorted(
        ((email, _score_email(email, area, issue_type)) for email in emails),
        key=lambda item: item[1],
        reverse=True,
    )
    best_email, best_score = ranked[0]
    if best_score < 1.5:
        return None
    return best_email


def _unwrap_ddg_url(href: str) -> str:
    if "uddg=" in href:
        query = parse_qs(urlparse(href).query)
        return unquote(query.get("uddg", [href])[0])
    return href


def _parse_ddg_results(html: str) -> list[tuple[str, str]]:
    """Return (url, snippet_text) pairs from DuckDuckGo HTML."""
    results: list[tuple[str, str]] = []
    link_pattern = re.compile(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)>',
        re.IGNORECASE | re.DOTALL,
    )
    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)
    for idx, (href, _title) in enumerate(links):
        snippet = unescape(re.sub(r"<[^>]+>", " ", snippets[idx] if idx < len(snippets) else ""))
        results.append((_unwrap_ddg_url(href), snippet))
    return results[:6]


def _build_queries(area: GeoArea, issue_type: str) -> list[str]:
    place = _place_name(area)
    state = area.state or area.country or ""
    issue = issue_type.replace("_", " ")
    queries = [
        f'"{place}" municipal corporation official complaint email',
        f"{place} {state} corporation grievance contact email",
        f"{place} {issue} municipal corporation email contact",
    ]
    if state:
        queries.append(f"{place} nagar nigam {state} official email")
    return queries


async def _ddg_search(query: str) -> str:
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        response = await client.post(
            DDG_URL,
            data={"q": query, "kl": "wt-wt"},
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.text


async def _fetch_page_text(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        return ""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": USER_AGENT})
            if response.status_code != 200:
                return ""
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text" not in content_type:
                return ""
            return response.text[:400_000]
    except Exception as exc:
        logger.debug("Could not fetch %s: %s", url, exc)
        return ""


async def discover_authority_online(
    area: GeoArea,
    description: str,
    *,
    issue_type: str | None = None,
) -> ClassificationResult | None:
    """Search the public web for an official municipal complaint email near the reported location."""
    issue = issue_type or _classify_issue_type(description)
    place = _place_name(area)
    collected: list[str] = []
    pages_checked = 0

    for query in _build_queries(area, issue):
        try:
            html = await _ddg_search(query)
        except Exception as exc:
            logger.warning("DuckDuckGo search failed for %r: %s", query, exc)
            continue

        collected.extend(_extract_emails(html))

        for url, snippet in _parse_ddg_results(html):
            collected.extend(_extract_emails(snippet))
            if pages_checked >= 3:
                continue
            if not any(token in url.lower() for token in ("gov", "municipal", "corporation", "mc", "nigam", "tmc")):
                continue
            page_text = await _fetch_page_text(url)
            if page_text:
                collected.extend(_extract_emails(page_text))
                pages_checked += 1

        best = _pick_best_email(collected, area, issue)
        if best:
            department = f"{place} Municipal Corporation"
            if area.state:
                department = f"{department} ({area.state})"
            return ClassificationResult(
                issue_type=issue,
                department=department,
                department_email=best,
                confidence=0.88,
                reasoning=(
                    f"Found official contact {best} via web search for {place}, {area.state or area.country}."
                ),
                authority_source="web_search",
            )

    return None


async def discover_with_timeout(
    area: GeoArea,
    description: str,
    *,
    issue_type: str | None = None,
    timeout_seconds: float = 15.0,
) -> ClassificationResult | None:
    try:
        return await asyncio.wait_for(
            discover_authority_online(area, description, issue_type=issue_type),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.warning("Web authority discovery timed out for %s", _place_name(area))
        return None
