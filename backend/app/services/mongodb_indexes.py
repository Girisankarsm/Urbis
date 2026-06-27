"""MongoDB index creation for query performance."""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.petitions.create_index([("created_at", -1)])
    await db.petitions.create_index([("status", 1), ("created_at", -1)])
    await db.petitions.create_index([("reporter_user_id", 1), ("created_at", -1)])
    await db.petitions.create_index([("location.lat", 1), ("location.lng", 1)])
    await db.petitions.create_index([("issue_type", 1)])
    await db.petitions.create_index([("severity_score", -1)])
    await db.activity_log.create_index([("petition_id", 1), ("timestamp", 1)])
    logger.info("MongoDB indexes ensured")
