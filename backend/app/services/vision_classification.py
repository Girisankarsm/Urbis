"""AI vision classification for civic issue photos."""

from __future__ import annotations

import logging
from typing import Any

from app.services import lemma_service
from app.services.departments import ISSUE_KEYWORDS

logger = logging.getLogger(__name__)

VISION_ISSUE_TYPES = [
    "pothole",
    "garbage",
    "streetlight",
    "water_leak",
    "fallen_tree",
    "manhole",
    "illegal_dumping",
    "road_damage",
    "other",
]

_ISSUE_ALIASES = {
    "broken_streetlight": "streetlight",
    "water_leakage": "water_leak",
    "open_manhole": "manhole",
    "tree": "fallen_tree",
    "dumping": "illegal_dumping",
    "road": "road_damage",
}


def normalize_issue_type(raw: str) -> str:
    key = (raw or "other").strip().lower().replace(" ", "_").replace("-", "_")
    return _ISSUE_ALIASES.get(key, key if key in VISION_ISSUE_TYPES else "other")


def _keyword_classify(description: str) -> dict[str, Any]:
    text = (description or "").lower()
    scores: dict[str, int] = {k: 0 for k in VISION_ISSUE_TYPES if k != "other"}
    extended_keywords = {
        **ISSUE_KEYWORDS,
        "fallen_tree": ["fallen tree", "tree fallen", "branch", "uprooted"],
        "manhole": ["manhole", "open manhole", "sewer cover"],
        "illegal_dumping": ["illegal dump", "dumping", "debris pile"],
        "road_damage": ["road damage", "cracked road", "broken pavement", "asphalt"],
    }
    for issue_type, keywords in extended_keywords.items():
        for kw in keywords:
            if kw in text:
                scores[issue_type] = scores.get(issue_type, 0) + 2 if " " in kw else 1

    best = max(scores, key=scores.get) if scores else "other"
    if scores.get(best, 0) == 0:
        best = "other"
    confidence = min(0.85, 0.45 + scores.get(best, 0) * 0.12)
    return {
        "issue_type": normalize_issue_type(best),
        "confidence": round(confidence, 2),
        "reasoning": (
            f"Matched description keywords for '{best.replace('_', ' ')}'."
            if best != "other"
            else "No strong visual or text signals — classified as other."
        ),
        "source": "keyword",
    }


async def _classify_with_lemma(photo_url: str, description: str) -> dict[str, Any] | None:
    if not lemma_service.is_lemma_available():
        return None
    prompt = f"""Analyze this civic issue photo and classify it.

Photo URL: {photo_url}
Description: {description or 'See photo'}

Return ONLY valid JSON:
{{
  "issue_type": "one of {', '.join(VISION_ISSUE_TYPES)}",
  "confidence": 0.0-1.0,
  "reasoning": "what you see in the image"
}}
"""
    try:
        result = await lemma_service.run_agent("issue-classifier", prompt)
        if not result.get("issue_type"):
            return None
        return {
            "issue_type": normalize_issue_type(str(result["issue_type"])),
            "confidence": float(result.get("confidence", 0.65)),
            "reasoning": str(result.get("reasoning", "Lemma vision classification.")),
            "source": "lemma_vision",
        }
    except Exception as exc:
        logger.warning("Lemma vision classification error: %s", exc)
        return None


async def classify_image(
    photo_url: str,
    *,
    description: str = "",
) -> dict[str, Any]:
    """Classify a civic issue image. Tries Lemma issue-classifier, then keyword fallback."""
    result = await _classify_with_lemma(photo_url, description)
    if result:
        result["confidence"] = round(min(1.0, max(0.0, float(result["confidence"]))), 2)
        return result

    fallback = _keyword_classify(description)
    fallback["confidence"] = round(fallback["confidence"], 2)
    return fallback
