from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> dict[str, Any] | None:
    return await db.users.find_one({"_id": user_id})


async def upsert_google_user(
    db: AsyncIOMotorDatabase,
    *,
    userinfo: dict[str, Any],
    refresh_token: str | None,
) -> dict[str, Any]:
    google_id = userinfo["sub"]
    existing = await db.users.find_one({"google_id": google_id})
    now = datetime.now(timezone.utc)

    if existing:
        user_id = existing["_id"]
        update: dict[str, Any] = {
            "email": userinfo.get("email", existing.get("email", "")),
            "name": userinfo.get("name", existing.get("name", "")),
            "picture": userinfo.get("picture", existing.get("picture", "")),
            "updated_at": now,
        }
        if refresh_token:
            update["google_refresh_token"] = refresh_token
        await db.users.update_one({"_id": user_id}, {"$set": update})
    else:
        user_id = str(uuid4())
        doc = {
            "_id": user_id,
            "google_id": google_id,
            "email": userinfo.get("email", ""),
            "name": userinfo.get("name", ""),
            "picture": userinfo.get("picture", ""),
            "google_refresh_token": refresh_token or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(doc)

    user = await get_user_by_id(db, user_id)
    assert user is not None
    return user


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["_id"],
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "can_send_gmail": bool(user.get("google_refresh_token")),
    }
