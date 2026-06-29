"""Community hub — public reports and upvotes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.petitions import _serialize

PUBLIC_STATUSES = frozenset({"submitted", "under_review", "resolved", "escalated"})

_HUB_FIELDS = {
    "issue_type",
    "photo_url",
    "description",
    "location",
    "area_info",
    "status",
    "severity_score",
    "severity_level",
    "created_at",
    "submitted_at",
    "reporter_name",
}


def _public_query() -> dict[str, Any]:
    return {"status": {"$in": sorted(PUBLIC_STATUSES)}}


def _hub_summary(doc: dict[str, Any], *, upvote_count: int, upvoted: bool) -> dict[str, Any]:
    base = _serialize(doc)
    summary = {k: base[k] for k in _HUB_FIELDS if k in base}
    summary["id"] = base.get("id")
    summary["upvote_count"] = upvote_count
    summary["upvoted_by_me"] = upvoted
    area = summary.get("area_info") or {}
    summary["area_label"] = (
        area.get("display_name")
        or area.get("city")
        or area.get("municipality")
        or (summary.get("location") or {}).get("address")
        or "Unknown area"
    )
    reporter = (base.get("reporter_name") or "").strip()
    summary["reporter_display"] = reporter.split()[0] if reporter else "Citizen"
    return summary


async def list_hub_reports(
    db: AsyncIOMotorDatabase,
    *,
    sort: str = "popular",
    limit: int = 50,
    viewer_user_id: str | None = None,
) -> list[dict[str, Any]]:
    sort_key = [("upvote_count", -1), ("submitted_at", -1), ("created_at", -1)]
    if sort == "recent":
        sort_key = [("submitted_at", -1), ("created_at", -1)]

    cursor = db.petitions.find(_public_query()).sort(sort_key).limit(min(limit, 100))
    reports: list[dict[str, Any]] = []
    async for doc in cursor:
        pid = str(doc["_id"])
        upvote_count = int(doc.get("upvote_count") or 0)
        upvoted = False
        if viewer_user_id:
            upvoted = await db.petition_upvotes.find_one(
                {"petition_id": pid, "user_id": viewer_user_id}
            ) is not None
        reports.append(_hub_summary(doc, upvote_count=upvote_count, upvoted=upvoted))
    return reports


async def toggle_upvote(
    db: AsyncIOMotorDatabase,
    petition_id: str,
    user_id: str,
) -> dict[str, Any]:
    petition = await db.petitions.find_one({"_id": petition_id})
    if not petition:
        from bson import ObjectId

        try:
            petition = await db.petitions.find_one({"_id": ObjectId(petition_id)})
        except Exception:
            petition = None
    if not petition:
        raise ValueError("Report not found")
    if petition.get("status") not in PUBLIC_STATUSES:
        raise ValueError("Only filed community reports can be upvoted")

    pid = str(petition["_id"])
    existing = await db.petition_upvotes.find_one({"petition_id": pid, "user_id": user_id})
    now = datetime.now(timezone.utc)

    if existing:
        await db.petition_upvotes.delete_one({"_id": existing["_id"]})
        await db.petitions.update_one({"_id": petition["_id"]}, {"$inc": {"upvote_count": -1}})
        upvoted = False
    else:
        await db.petition_upvotes.insert_one(
            {"petition_id": pid, "user_id": user_id, "created_at": now}
        )
        await db.petitions.update_one({"_id": petition["_id"]}, {"$inc": {"upvote_count": 1}})
        upvoted = True

    updated = await db.petitions.find_one({"_id": petition["_id"]})
    count = max(0, int((updated or {}).get("upvote_count") or 0))
    return {"petition_id": pid, "upvote_count": count, "upvoted_by_me": upvoted}
