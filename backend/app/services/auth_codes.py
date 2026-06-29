import secrets
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

AUTH_CODE_TTL_SECONDS = 300


async def create_auth_code(db: AsyncIOMotorDatabase, *, user_id: str) -> str:
    code = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    await db.auth_codes.insert_one(
        {
            "_id": code,
            "user_id": user_id,
            "created_at": now,
            "expires_at": now + timedelta(seconds=AUTH_CODE_TTL_SECONDS),
        }
    )
    return code


async def consume_auth_code(db: AsyncIOMotorDatabase, code: str) -> str | None:
    if not code:
        return None
    now = datetime.now(timezone.utc)
    doc = await db.auth_codes.find_one_and_delete(
        {
            "_id": code,
            "expires_at": {"$gt": now},
        }
    )
    if not doc:
        return None
    return doc.get("user_id")
