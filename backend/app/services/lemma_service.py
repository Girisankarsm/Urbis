"""Lemma SDK client — agents, functions, and workflow helpers."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_resolved_token: str | None = None
_resolved_token_exp: float = 0.0
_refresh_task: asyncio.Task[None] | None = None

TOKEN_REFRESH_BUFFER_SECONDS = 300  # refresh 5 minutes before expiry


def _lemma_config_path() -> Path:
    raw = os.environ.get("LEMMA_CONFIG_FILE", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".lemma" / "config.json"


def _get_refresh_token() -> str:
    if settings.lemma_refresh_token.strip():
        return settings.lemma_refresh_token.strip()

    config_path = _lemma_config_path()
    if not config_path.is_file():
        return ""

    try:
        data = json.loads(config_path.read_text())
        server = data.get("active_server", "default")
        servers = data.get("servers", {})
        server_cfg = servers.get(server, {}) if isinstance(servers, dict) else {}
        auth = server_cfg.get("auth", {}) if isinstance(server_cfg.get("auth"), dict) else {}
        return str(auth.get("refresh_token") or server_cfg.get("refresh_token") or "").strip()
    except (json.JSONDecodeError, OSError, AttributeError, TypeError) as exc:
        logger.debug("Could not read Lemma CLI config: %s", exc)
        return ""


def _token_expiry(token: str) -> float:
    if token.count(".") != 2:
        return 0.0
    return float(_decode_jwt_payload(token).get("exp") or 0)


def _token_needs_refresh(token: str) -> bool:
    if not token:
        return True
    exp = _token_expiry(token)
    if not exp:
        return False
    return time.time() >= exp - TOKEN_REFRESH_BUFFER_SECONDS


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, json.JSONDecodeError, ValueError):
        return {}


def lemma_token_status() -> dict[str, Any]:
    """Report whether Lemma credentials are present and the session token is still valid."""
    if not settings.lemma_enabled:
        return {
            "configured": False,
            "token_valid": False,
            "reason": "Set LEMMA_POD_ID and LEMMA_REFRESH_TOKEN (or LEMMA_TOKEN) in .env",
        }

    refresh_token = _get_refresh_token()
    token = settings.lemma_token.strip()
    if refresh_token and not token:
        return {
            "configured": True,
            "token_valid": True,
            "token_type": "auto_refresh",
            "reason": "Refresh token configured — access token fetched automatically",
        }
    parts = token.split(".")
    if len(parts) == 3 and not token.startswith("ey"):
        return {
            "configured": True,
            "token_valid": False,
            "token_type": "session",
            "reason": "LEMMA_TOKEN looks truncated — JWT must start with eyJ. Run ./scripts/lemma-env-hint.sh",
        }
    if len(parts) != 3:
        return {
            "configured": True,
            "token_valid": False,
            "token_type": "api_key",
            "reason": "API key configured — verify with /api/health/lemma",
        }

    claims = _decode_jwt_payload(token)
    exp = claims.get("exp")
    if not exp:
        return {
            "configured": True,
            "token_valid": True,
            "token_type": "opaque",
            "reason": "Non-expiring token configured (verify with /api/health/lemma)",
        }

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    if time.time() >= exp:
        if _get_refresh_token():
            return {
                "configured": True,
                "token_valid": True,
                "token_type": "auto_refresh",
                "reason": "Session expired in .env — will auto-refresh on next request",
                "expires_at": expires_at.isoformat(),
            }
        return {
            "configured": True,
            "token_valid": False,
            "token_type": "session",
            "reason": "Lemma session token expired — create a dashboard API key or run `lemma auth login`",
            "expires_at": expires_at.isoformat(),
        }

    return {
        "configured": True,
        "token_valid": True,
        "token_type": "session",
        "expires_at": expires_at.isoformat(),
        "expires_in_seconds": int(exp - time.time()),
    }


async def _fetch_fresh_access_token(refresh_token: str) -> str:
    from lemma_sdk.auth import refresh_cli_session

    session = await asyncio.to_thread(
        refresh_cli_session,
        base_url=settings.lemma_base_url,
        refresh_token=refresh_token,
        verify_ssl=True,
        timeout=30.0,
    )
    new_token = (session.get("access_token") or session.get("token") or "").strip()
    if not new_token:
        raise RuntimeError("Lemma refresh succeeded but returned no access token")
    return new_token


async def resolve_lemma_token(*, force_refresh: bool = False) -> str:
    """Return a Lemma bearer token, auto-refreshing from LEMMA_REFRESH_TOKEN when needed."""
    global _resolved_token, _resolved_token_exp

    refresh_token = _get_refresh_token()
    token = settings.lemma_token.strip()

    if (
        not force_refresh
        and _resolved_token
        and _resolved_token_exp > time.time() + 60
    ):
        return _resolved_token

    if not force_refresh and token and not _token_needs_refresh(token):
        return token

    if refresh_token:
        new_token = await _fetch_fresh_access_token(refresh_token)
        _resolved_token = new_token
        _resolved_token_exp = _token_expiry(new_token)
        logger.info("Lemma access token refreshed automatically")
        return new_token

    if token:
        return token

    raise RuntimeError(
        "Lemma not configured — set LEMMA_REFRESH_TOKEN in .env (run ./scripts/lemma-env-hint.sh)"
    )


async def warm_lemma_token() -> None:
    """Refresh Lemma credentials on API startup."""
    if not settings.lemma_enabled:
        return
    await resolve_lemma_token(force_refresh=bool(_get_refresh_token()))


async def _lemma_refresh_loop() -> None:
    while True:
        await asyncio.sleep(600)
        if not settings.lemma_enabled:
            continue
        try:
            await resolve_lemma_token()
        except Exception as exc:
            logger.warning("Background Lemma token refresh failed: %s", exc)


def start_lemma_token_refresh_loop() -> None:
    global _refresh_task
    if not settings.lemma_enabled or _refresh_task is not None:
        return
    _refresh_task = asyncio.create_task(_lemma_refresh_loop())


async def stop_lemma_token_refresh_loop() -> None:
    global _refresh_task
    if _refresh_task is None:
        return
    _refresh_task.cancel()
    try:
        await _refresh_task
    except asyncio.CancelledError:
        pass
    _refresh_task = None


async def verify_lemma_api() -> dict[str, Any]:
    """Ping Lemma API to confirm the pod is reachable with the current token."""
    status = lemma_token_status()
    if not status.get("configured"):
        return {**status, "api_reachable": False}

    url = f"{settings.lemma_base_url.rstrip('/')}/pods/{settings.lemma_pod_id}"
    try:
        token = await resolve_lemma_token()
    except Exception as exc:
        return {
            **status,
            "token_valid": False,
            "api_reachable": False,
            "reason": str(exc),
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            pod = resp.json()
            return {
                **status,
                "token_valid": True,
                "api_reachable": True,
                "pod_name": pod.get("name"),
            }
        if resp.status_code == 401:
            return {
                **status,
                "token_valid": False,
                "api_reachable": False,
                "reason": (
                    "Lemma rejected the token (401). Use `lemma auth print-token` for LEMMA_TOKEN "
                    "and copy refresh_token from ~/.lemma/config.json into LEMMA_REFRESH_TOKEN."
                ),
            }
        return {
            **status,
            "token_valid": False,
            "api_reachable": False,
            "reason": f"Lemma API returned {resp.status_code}",
        }
    except Exception as exc:
        return {**status, "api_reachable": False, "reason": f"Lemma API unreachable: {exc}"}


def is_lemma_available() -> bool:
    return settings.lemma_enabled


def _build_pod(token: str):
    from lemma_sdk import Pod

    return Pod(
        pod_id=settings.lemma_pod_id,
        org_id=settings.lemma_org_id or None,
        token=token,
        base_url=settings.lemma_base_url,
    )


def _parse_json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"raw": text}


def _run_agent_sync(agent_name: str, message: str, *, token: str, timeout: int = 180) -> dict[str, Any]:
    pod = _build_pod(token)
    conv = pod.agents.run(agent_name, message)
    conv_id = str(conv.to_dict()["id"])
    deadline = time.time() + timeout

    while time.time() < deadline:
        detail = pod.conversations.get(conv_id).to_dict()
        status = str(detail.get("status") or detail.get("last_run_status") or "").upper()
        if status in {"COMPLETED", "IDLE", "FAILED", "CANCELLED"}:
            break
        time.sleep(2)

    messages = pod.conversations.messages(conv_id, limit=50).to_dict().get("items", [])
    assistant_text = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("text"):
            assistant_text = msg["text"]
            break

    return _parse_json_from_text(assistant_text)


async def run_agent(agent_name: str, message: str) -> dict[str, Any]:
    token = await resolve_lemma_token()
    return await asyncio.to_thread(_run_agent_sync, agent_name, message, token=token)


def _run_function_sync(name: str, payload: dict[str, Any], *, token: str) -> dict[str, Any]:
    pod = _build_pod(token)
    result = pod.functions.run(name, payload).to_dict()
    output = result.get("output_data") or {}
    if isinstance(output, dict):
        return output
    return {"result": output}


async def run_function(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = await resolve_lemma_token()
    return await asyncio.to_thread(_run_function_sync, name, payload, token=token)


async def classify_with_lemma(
    *,
    petition_id: str,
    photo_url: str,
    description: str,
    lat: float,
    lng: float,
    address: str,
    area_display: str,
    city: str,
    municipality: str,
    district: str = "",
    suburb: str = "",
    state: str,
    country: str,
) -> dict[str, Any]:
    prompt = f"""Classify this civic issue and find the correct government authority contact email for the reported location.

Petition ID: {petition_id}
Photo URL: {photo_url}
Description: {description or 'See photo'}
Coordinates: {lat}, {lng}
Address hint: {address or area_display}
Area: {area_display}
City: {city}
District: {district or municipality}
Suburb/locality: {suburb or address}
State: {state}
Country: {country}

Instructions:
1. Use WEB_SEARCH to find the official municipal/government complaint email for this area and issue type.
2. Search queries like: "{{city}} {{municipality}} civic complaint email", "{{city}} pothole report contact", "{{municipality}} sanitation department email"
3. Prefer official .gov / .gov.in / municipal corporation emails over random blogs.
4. Update the petition record in the POD with issue_type, department, department_email.
5. Log a classified event in activity_log.

Return ONLY valid JSON:
{{
  "issue_type": "pothole|garbage|streetlight|water_leak|sewage|other",
  "department": "Full authority name",
  "department_email": "official@email",
  "confidence": 0.0-1.0,
  "reasoning": "How you identified the authority",
  "area_searched": "{city}, {state}"
}}
"""
    return await run_agent("issue-classifier", prompt)


async def draft_email_with_lemma(*, petition_id: str) -> dict[str, Any]:
    prompt = f"""Draft a formal citizen complaint email for petition {petition_id}.

Use POD tools to read the petition (issue, location, department, photo).
Update complaint_email_subject and complaint_email_draft on the petition.
Log drafted and approval_pending events.

Return ONLY valid JSON:
{{
  "subject": "...",
  "body": "full email body",
  "to_email": "authority email"
}}
"""
    return await run_agent("complaint-drafter", prompt)


async def send_email_with_lemma(
    *,
    petition_id: str,
    subject: str,
    body: str,
    to_email: str,
    approved: bool = True,
    is_escalation: bool = False,
) -> dict[str, Any]:
    return await run_function(
        "send_complaint_email",
        {
            "petition_id": petition_id,
            "subject": subject,
            "body": body,
            "to_email": to_email,
            "approved": approved,
            "is_escalation": is_escalation,
        },
    )
