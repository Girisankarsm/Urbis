"""Resolve government authority contact for a geographic area and issue type."""

from __future__ import annotations

import logging
import re

from app.models import ClassificationResult
from app.services.departments import ISSUE_KEYWORDS
from app.services.geocoding import GeoArea
from app.services.regional_authorities import (
    INDIA_STATE_CONTACTS,
    METRO_ALIASES,
    REGIONAL_CONTACTS,
)

logger = logging.getLogger(__name__)


def _classify_issue_type(description: str) -> str:
    text = description.lower()
    scores = {k: 0 for k in ISSUE_KEYWORDS}
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[issue_type] += 2 if " " in kw else 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def _area_haystack(area: GeoArea) -> str:
    parts = (
        area.display_name,
        area.city,
        area.district,
        area.suburb,
        area.municipality,
        area.state,
        area.country,
        area.postcode,
    )
    return " ".join(p for p in parts if p).lower()


def _normalize_state(state: str) -> str:
    return state.strip().lower().replace("&", "and")


def _match_direct_region(haystack: str) -> str | None:
    """Match known city/corporation names — prefer longer keys (e.g. new delhi before delhi)."""
    for key in sorted(REGIONAL_CONTACTS.keys(), key=len, reverse=True):
        if key in haystack:
            return key
    return None


def _match_metro_alias(haystack: str) -> str | None:
    """Suburbs that geocode without the main city name."""
    for parent, aliases in METRO_ALIASES.items():
        if parent not in REGIONAL_CONTACTS:
            continue
        if any(alias in haystack for alias in aliases):
            return parent
    return None


def _match_india_state(haystack: str, state: str) -> str | None:
    if "india" not in haystack and state:
        haystack = f"{haystack} {state.lower()}"
    normalized = _normalize_state(state)
    for state_key in sorted(INDIA_STATE_CONTACTS.keys(), key=len, reverse=True):
        if state_key in haystack or state_key in normalized:
            return state_key
    return None


def _contacts_for_region(region_key: str, issue: str) -> tuple[str, str]:
    contacts = REGIONAL_CONTACTS.get(region_key) or INDIA_STATE_CONTACTS.get(region_key, {})
    return contacts.get(issue, contacts["other"])


def _location_label(area: GeoArea) -> str:
    return (
        area.city
        or area.suburb
        or area.district
        or area.municipality
        or area.display_name.split(",")[0]
        or "your area"
    )


def resolve_region_key(area: GeoArea) -> tuple[str | None, str]:
    """Return (region_key, match_kind) where match_kind describes how we matched."""
    haystack = _area_haystack(area)

    direct = _match_direct_region(haystack)
    if direct:
        return direct, "city"

    metro = _match_metro_alias(haystack)
    if metro:
        return metro, "metro"

    if area.country.lower() in {"india", "भारत"} or "india" in haystack:
        state_key = _match_india_state(haystack, area.state)
        if state_key:
            return state_key, "state"

    return None, "none"


def lookup_authority(area: GeoArea, description: str, issue_type: str | None = None) -> ClassificationResult:
    issue = issue_type or _classify_issue_type(description)
    region_key, match_kind = resolve_region_key(area)
    label = _location_label(area)

    if region_key:
        dept_name, email = _contacts_for_region(region_key, issue)
        match_labels = {
            "city": f"city/municipality ({region_key})",
            "metro": f"metro area near {region_key}",
            "state": f"state ({region_key})",
        }
        return ClassificationResult(
            issue_type=issue,
            department=dept_name,
            department_email=email,
            confidence=0.9 if match_kind == "city" else 0.8 if match_kind == "metro" else 0.7,
            reasoning=(
                f"Located complaint in {label}, {area.state or area.country}. "
                f"Matched {match_labels[match_kind]} and routed to {dept_name}."
            ),
            authority_source="registry",
        )

    label = _location_label(area)
    return ClassificationResult(
        issue_type=issue,
        department=f"Municipal Authority ({label})",
        department_email="",
        confidence=0.2,
        reasoning=(
            f"No cached authority for {label}, {area.state or area.country}. "
            "Web search or manual verification required before sending."
        ),
        authority_source="unknown",
    )


def merge_lemma_classification(
    lemma_result: dict,
    area: GeoArea,
    description: str,
) -> ClassificationResult:
    email = lemma_result.get("department_email", "")
    if email and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return ClassificationResult(
            issue_type=lemma_result.get("issue_type") or _classify_issue_type(description),
            department=lemma_result.get("department") or "Municipal Authority",
            department_email=email,
            confidence=float(lemma_result.get("confidence", 0.8)),
            reasoning=lemma_result.get(
                "reasoning",
                "Lemma agent identified authority via knowledge base and web search.",
            ),
            authority_source="lemma",
        )
    return lookup_authority(area, description, lemma_result.get("issue_type"))
