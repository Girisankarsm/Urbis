"""Duplicate complaint detection — nearby reports with similar issue type."""

from __future__ import annotations

import hashlib
import io
import logging
import math
from typing import Any

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _average_hash(image_bytes: bytes, hash_size: int = 8) -> str:
    """Simple perceptual hash for image similarity (no Pillow required)."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((hash_size, hash_size))
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = "".join("1" if p >= avg else "0" for p in pixels)
        return bits
    except Exception:
        return hashlib.md5(image_bytes[:8192]).hexdigest()


def _hash_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if all(c in "01" for c in a) and len(a) == len(b):
        matches = sum(1 for x, y in zip(a, b) if x == y)
        return matches / len(a)
    return 1.0 if a == b else 0.0


async def _fetch_image_bytes(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            return resp.content
    except Exception as exc:
        logger.debug("Could not fetch image for duplicate check: %s", exc)
    return None


async def find_nearby_duplicates(
    db: AsyncIOMotorDatabase,
    *,
    lat: float,
    lng: float,
    issue_type: str | None = None,
    photo_url: str | None = None,
    radius_m: float | None = None,
    exclude_id: str | None = None,
) -> list[dict[str, Any]]:
    """Find likely duplicate petitions near the given location."""
    radius = radius_m or settings.duplicate_radius_m
    delta = radius / 111_000.0
    query: dict[str, Any] = {
        "location.lat": {"$gte": lat - delta, "$lte": lat + delta},
        "location.lng": {"$gte": lng - delta, "$lte": lng + delta},
        "status": {"$nin": ["draft"]},
    }
    if exclude_id:
        query["_id"] = {"$ne": exclude_id}

    candidates: list[dict[str, Any]] = []
    cursor = db.petitions.find(query).sort("created_at", -1).limit(50)

    photo_hash: str | None = None
    if photo_url:
        img_bytes = await _fetch_image_bytes(photo_url)
        if img_bytes:
            photo_hash = _average_hash(img_bytes)

    async for doc in cursor:
        loc = doc.get("location") or {}
        plat, plng = loc.get("lat"), loc.get("lng")
        if plat is None or plng is None:
            continue
        distance_m = _haversine_m(lat, lng, float(plat), float(plng))
        if distance_m > radius:
            continue

        doc_issue = doc.get("issue_type") or "other"
        same_type = not issue_type or doc_issue == issue_type or issue_type == "other"

        image_similarity = 0.0
        if photo_hash and doc.get("photo_url"):
            other_bytes = await _fetch_image_bytes(doc["photo_url"])
            if other_bytes:
                other_hash = _average_hash(other_bytes)
                image_similarity = _hash_similarity(photo_hash, other_hash)

        likelihood = 0.0
        if same_type:
            likelihood += 0.5
        if distance_m < radius * 0.3:
            likelihood += 0.25
        if image_similarity >= 0.85:
            likelihood += 0.35
        elif image_similarity >= 0.7:
            likelihood += 0.15

        if likelihood < 0.5:
            continue

        candidates.append(
            {
                "petition_id": str(doc["_id"]),
                "issue_type": doc_issue,
                "status": doc.get("status"),
                "distance_m": round(distance_m, 1),
                "image_similarity": round(image_similarity, 2) if photo_hash else None,
                "likelihood": round(min(1.0, likelihood), 2),
                "photo_url": doc.get("photo_url"),
                "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
                "description": (doc.get("description") or "")[:120],
            }
        )

    candidates.sort(key=lambda c: c["likelihood"], reverse=True)
    return candidates[:5]
