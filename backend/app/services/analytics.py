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


async def infrastructure_analytics(
    db: AsyncIOMotorDatabase,
    *,
    proximity_m: int = 500,
    high_risk_threshold: float = 25,
) -> dict[str, Any]:
    """Infrastructure-aware analytics extensions."""
    school_near = await db.petitions.count_documents(
        {
            "infrastructure.distance_to_school": {"$lte": proximity_m, "$ne": None},
        }
    )
    hospital_near = await db.petitions.count_documents(
        {
            "infrastructure.distance_to_hospital": {"$lte": proximity_m, "$ne": None},
        }
    )

    buckets = {"under_100m": [], "100_300m": [], "300_500m": []}
    async for doc in db.petitions.find(
        {"infrastructure.distance_to_school": {"$ne": None}, "severity_score": {"$exists": True}},
        {"severity_score": 1, "infrastructure.distance_to_school": 1},
    ):
        dist = doc.get("infrastructure", {}).get("distance_to_school")
        score = doc.get("severity_score")
        if dist is None or score is None:
            continue
        if dist < 100:
            buckets["under_100m"].append(score)
        elif dist < 300:
            buckets["100_300m"].append(score)
        elif dist < 500:
            buckets["300_500m"].append(score)

    def avg(vals: list) -> float | None:
        return round(sum(vals) / len(vals), 1) if vals else None

    high_risk = await db.petitions.count_documents(
        {"infrastructure.infra_score": {"$gte": high_risk_threshold}}
    )

    school_scores = []
    hospital_scores = []
    async for doc in db.petitions.find(
        {"severity_score": {"$exists": True}, "infrastructure": {"$exists": True}},
        {"severity_score": 1, "infrastructure": 1},
    ):
        infra = doc.get("infrastructure") or {}
        score = doc.get("severity_score")
        if score is None:
            continue
        if infra.get("distance_to_school") is not None:
            school_scores.append(score)
        if infra.get("distance_to_hospital") is not None:
            hospital_scores.append(score)

    return {
        "proximity_radius_m": proximity_m,
        "complaints_near_schools": school_near,
        "complaints_near_hospitals": hospital_near,
        "severity_by_school_proximity": {
            "under_100m": {"count": len(buckets["under_100m"]), "avg_severity": avg(buckets["under_100m"])},
            "100_300m": {"count": len(buckets["100_300m"]), "avg_severity": avg(buckets["100_300m"])},
            "300_500m": {"count": len(buckets["300_500m"]), "avg_severity": avg(buckets["300_500m"])},
        },
        "high_risk_zones": {
            "threshold_infra_score": high_risk_threshold,
            "count": high_risk,
        },
        "avg_severity_near_schools": avg(school_scores),
        "avg_severity_near_hospitals": avg(hospital_scores),
    }


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
        "infrastructure": await infrastructure_analytics(db),
    }
