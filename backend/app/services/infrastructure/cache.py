"""MongoDB TTL cache for Overpass results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.infrastructure.overpass_service import fetch_overpass_elements

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


def cache_key(lat: float, lng: float, radius_m: int) -> str:
    return f"overpass:{round(lat, 4)}:{round(lng, 4)}:{radius_m}"


async def ensure_overpass_cache_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.overpass_cache.create_index("key", unique=True)
    await db.overpass_cache.create_index(
        "expires_at",
        expireAfterSeconds=0,
    )


async def get_cached_overpass(
    db: AsyncIOMotorDatabase,
    lat: float,
    lng: float,
    radius_m: int,
) -> dict[str, Any]:
    """Return {data, source} — source is cache | overpass | overpass_mirror | unavailable."""
    key = cache_key(lat, lng, radius_m)
    try:
        doc = await db.overpass_cache.find_one({"key": key})
        if doc and doc.get("elements") is not None:
            return {"data": doc["elements"], "source": "cache"}
    except Exception as exc:
        logger.warning("Overpass cache read failed: %s", exc)

    result = await fetch_overpass_elements(lat, lng, radius_m)
    if result.get("data") is not None:
        try:
            now = datetime.now(timezone.utc)
            from datetime import timedelta

            expires = now + timedelta(seconds=CACHE_TTL_SECONDS)
            await db.overpass_cache.update_one(
                {"key": key},
                {
                    "$set": {
                        "key": key,
                        "lat": round(lat, 4),
                        "lng": round(lng, 4),
                        "radius_m": radius_m,
                        "elements": result["data"],
                        "source": result["source"],
                        "fetched_at": now,
                        "expires_at": expires,
                    }
                },
                upsert=True,
            )
        except Exception as exc:
            logger.warning("Overpass cache write failed: %s", exc)

    return result
