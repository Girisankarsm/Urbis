from fastapi import APIRouter, Query

from app.database import get_db
from app.services.analytics import (
    analytics_summary,
    common_issue_types,
    complaint_trends,
    department_performance,
    resolution_time_stats,
    severity_distribution,
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def get_summary():
    db = get_db()
    return await analytics_summary(db)


@router.get("/trends")
async def get_trends(days: int = Query(30, ge=1, le=365)):
    db = get_db()
    return await complaint_trends(db, days=days)


@router.get("/severity")
async def get_severity_distribution():
    db = get_db()
    return await severity_distribution(db)


@router.get("/resolution-time")
async def get_resolution_time():
    db = get_db()
    return await resolution_time_stats(db)


@router.get("/issue-types")
async def get_issue_types(limit: int = Query(10, ge=1, le=50)):
    db = get_db()
    return {"items": await common_issue_types(db, limit=limit)}


@router.get("/departments")
async def get_department_performance():
    db = get_db()
    return {"items": await department_performance(db)}
