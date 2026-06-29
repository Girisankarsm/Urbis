"""Resolution verification — compare original and follow-up images."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.config import settings
from app.services import lemma_service
from app.services.ai import check_resolution

logger = logging.getLogger(__name__)

RESOLUTION_STATUSES = ("resolved", "partially_resolved", "not_resolved")


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


async def _verify_with_openai(
    original_url: str,
    follow_up_url: str,
    issue_type: str,
    description: str,
) -> dict[str, Any] | None:
    if not settings.openai_api_key.strip():
        return None
    prompt = (
        f"Compare these two civic issue photos (before and after). Issue type: {issue_type}. "
        f"Description: {description or 'N/A'}. "
        "Determine if the issue is resolved, partially resolved, or not resolved. "
        'Return JSON only: {"status":"resolved|partially_resolved|not_resolved",'
        '"confidence":0.0-1.0,"reasoning":"..."}'
    )
    payload = {
        "model": settings.vision_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": original_url}},
                    {"type": "image_url", "image_url": {"url": follow_up_url}},
                ],
            }
        ],
        "max_tokens": 350,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.vision_timeout_seconds) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=payload,
            )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        data = _parse_json(content)
        status = str(data.get("status", "")).lower()
        if status not in RESOLUTION_STATUSES:
            return None
        return {
            "status": status,
            "resolved": status == "resolved",
            "confidence": float(data.get("confidence", 0.7)),
            "reasoning": str(data.get("reasoning", "Visual comparison of before/after photos.")),
            "source": "openai_vision",
        }
    except Exception as exc:
        logger.warning("OpenAI resolution verification error: %s", exc)
        return None


async def _verify_with_lemma(
    original_url: str,
    follow_up_url: str,
    issue_type: str,
    description: str,
) -> dict[str, Any] | None:
    if not lemma_service.is_lemma_available():
        return None
    prompt = f"""Compare the original and follow-up civic issue photos.

Issue type: {issue_type}
Description: {description or 'N/A'}
Original photo: {original_url}
Follow-up photo: {follow_up_url}

Return ONLY valid JSON:
{{
  "status": "resolved|partially_resolved|not_resolved",
  "confidence": 0.0-1.0,
  "reasoning": "comparison explanation"
}}
"""
    try:
        result = await lemma_service.run_agent("resolution-checker", prompt)
        status = str(result.get("status", "")).lower()
        if status not in RESOLUTION_STATUSES:
            resolved = bool(result.get("resolved"))
            status = "resolved" if resolved else "not_resolved"
        return {
            "status": status,
            "resolved": status == "resolved",
            "confidence": float(result.get("confidence", 0.65)),
            "reasoning": str(result.get("reasoning", "Lemma resolution-checker analysis.")),
            "source": "lemma_resolution_checker",
        }
    except Exception as exc:
        logger.warning("Lemma resolution verification error: %s", exc)
        return None


def _heuristic_verdict(issue_type: str, description: str) -> dict[str, Any]:
    local = check_resolution(issue_type, description)
    status = "resolved" if local.resolved else "not_resolved"
    return {
        "status": status,
        "resolved": local.resolved,
        "confidence": local.confidence,
        "reasoning": local.reasoning,
        "recommended_status": local.recommended_status,
        "source": "heuristic",
    }


async def verify_resolution(
    *,
    original_url: str,
    follow_up_url: str,
    issue_type: str,
    description: str = "",
) -> dict[str, Any]:
    """Compare before/after images and return resolution verdict."""
    for verifier in (_verify_with_lemma, _verify_with_openai):
        result = await verifier(original_url, follow_up_url, issue_type, description)
        if result:
            result["confidence"] = round(min(1.0, max(0.0, float(result["confidence"]))), 2)
            result["recommended_status"] = (
                "resolved" if result["status"] == "resolved" else "under_review"
            )
            return result

    return _heuristic_verdict(issue_type, description)
