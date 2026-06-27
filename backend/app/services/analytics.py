"""Analytics aggregation for civic complaint data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


async def complaint_trends(db: AsyncIOMotorDatabase, days: int = 30) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    daily = [{"date": r["_id"], "count": r["count"]} async for r in db.petitions.aggregate(pipeline)]
    return {"period_days": days, "daily": daily, "total": sum(d["count"] for d in daily)}


async def severity_distribution(db: AsyncIOMotorDatabase) -> dict[str, Any]:
    pipeline = [
        {"$match": {"severity_score": {"$exists": True}}},
        {
            "$bucket": {
                "groupBy": "$severity_score",
                "boundaries": [0, 25, 50, 75, 101],
                "default": "unknown",
                "output": {"count": {"$sum": 1}},
            }
        },
    ]
    buckets = []
    labels = {0: "0-24", 25: "25-49", 50: "50-74", 75: "75-100"}
    async for r in db.petitions.aggregate(pipeline):
        bid = r["_id"]
        buckets.append({"range": labels.get(bid, str(bid)), "count": r["count"]})
    return {"buckets": buckets}


async def resolution_time_stats(db: AsyncIOMotorDatabase) -> dict[str, Any]:
    pipeline = [
        {
            "$match": {
                "resolved_at": {"$exists": True},
                "submitted_at": {"$exists": True},
            }
        },
        {
            "$project": {
                "hours": {
                    "$divide": [
                        {"$subtract": ["$resolved_at", "$submitted_at"]},
                        3600000,
                    ]
                }
            }
        },
    ]
    hours_list = [r["hours"] async for r in db.petitions.aggregate(pipeline) if r.get("hours") is not None]
    if not hours_list:
        return {"count": 0, "avg_hours": None, "median_hours": None}
    hours_list.sort()
    n = len(hours_list)
    median = hours_list[n // 2]
    return {
        "count": n,
        "avg_hours": round(sum(hours_list) / n, 1),
        "median_hours": round(median, 1),
    }


async def common_issue_types(db: AsyncIOMotorDatabase, limit: int = 10) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"issue_type": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$issue_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    return [{"issue_type": r["_id"], "count": r["count"]} async for r in db.petitions.aggregate(pipeline)]


async def department_performance(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"department": {"$exists": True, "$ne": None}}},
        {
            "$group": {
                "_id": "$department",
                "total": {"$sum": 1},
                "resolved": {"$sum": {"$cond": [{"$eq": ["$status", "resolved"]}, 1, 0]}},
                "escalated": {"$sum": {"$cond": [{"$eq": ["$status", "escalated"]}, 1, 0]}},
                "avg_severity": {"$avg": "$severity_score"},
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 20},
    ]
    results = []
    async for r in db.petitions.aggregate(pipeline):
        total = r["total"]
        resolved = r["resolved"]
        results.append(
            {
                "department": r["_id"],
                "total_complaints": total,
                "resolved": resolved,
                "escalated": r["escalated"],
                "resolution_rate": round(resolved / total, 2) if total else 0,
                "avg_severity": round(r["avg_severity"], 1) if r.get("avg_severity") else None,
            }
        )
    return results


async def analytics_summary(db: AsyncIOMotorDatabase) -> dict[str, Any]:
    total = await db.petitions.count_documents({})
    by_status = {}
    async for r in db.petitions.aggregate(
        [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    ):
        by_status[r["_id"] or "unknown"] = r["count"]

    return {
        "total_petitions": total,
        "by_status": by_status,
        "trends": await complaint_trends(db, days=30),
        "severity_distribution": await severity_distribution(db),
        "resolution_time": await resolution_time_stats(db),
        "common_issue_types": await common_issue_types(db),
        "department_performance": await department_performance(db),
    }
