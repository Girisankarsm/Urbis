"""Lemma SDK client — agents, functions, and workflow helpers."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_pod = None


def is_lemma_available() -> bool:
    return settings.lemma_enabled


def get_pod():
    global _pod
    if not settings.lemma_enabled:
        raise RuntimeError("Lemma is not configured — set LEMMA_TOKEN and LEMMA_POD_ID in .env")

    if _pod is None:
        from lemma_sdk import Pod

        _pod = Pod(
            pod_id=settings.lemma_pod_id,
            org_id=settings.lemma_org_id or None,
            token=settings.lemma_token,
            base_url=settings.lemma_base_url,
        )
    return _pod


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


def _run_agent_sync(agent_name: str, message: str, *, timeout: int = 180) -> dict[str, Any]:
    pod = get_pod()
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
    return await asyncio.to_thread(_run_agent_sync, agent_name, message)


def _run_function_sync(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    pod = get_pod()
    result = pod.functions.run(name, payload).to_dict()
    output = result.get("output_data") or {}
    if isinstance(output, dict):
        return output
    return {"result": output}


async def run_function(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_run_function_sync, name, payload)


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
