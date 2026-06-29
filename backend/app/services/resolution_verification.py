"""Resolution verification — compare original and follow-up images."""

from __future__ import annotations

import logging
from typing import Any

from app.services import lemma_service
from app.services.ai import check_resolution

logger = logging.getLogger(__name__)

RESOLUTION_STATUSES = ("resolved", "partially_resolved", "not_resolved")

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
    result = await _verify_with_lemma(original_url, follow_up_url, issue_type, description)
    if result:
        result["confidence"] = round(min(1.0, max(0.0, float(result["confidence"]))), 2)
        result["recommended_status"] = (
            "resolved" if result["status"] == "resolved" else "under_review"
        )
        return result

    return _heuristic_verdict(issue_type, description)
