"""Severity scoring — delegates to infrastructure analysis pipeline."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.infrastructure.analysis import analyze_infrastructure


async def analyze_severity(
    db: AsyncIOMotorDatabase,
    *,
    issue_type: str,
    lat: float,
    lng: float,
    description: str = "",
    vision_confidence: float = 0.5,
) -> dict[str, Any]:
    """Compute severity score 0–100 with nearby infrastructure context."""
    return await analyze_infrastructure(
        db,
        lat=lat,
        lng=lng,
        issue_type=issue_type,
        description=description,
        vision_confidence=vision_confidence,
    )
