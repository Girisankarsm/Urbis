from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import settings
from app.database import get_db
from app.dependencies import get_optional_user
from app.services.hub import list_hub_reports, toggle_upvote

router = APIRouter(prefix="/api/hub", tags=["hub"])


def _viewer_id(user: dict | None) -> str | None:
    if not user:
        return None
    return user.get("_id") or user.get("id")


@router.get("/reports")
async def hub_reports(
    sort: str = Query("popular", pattern="^(popular|recent)$"),
    limit: int = Query(50, ge=1, le=100),
    user: dict | None = Depends(get_optional_user),
):
    db = get_db()
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to browse the community hub")
    viewer = _viewer_id(user)
    reports = await list_hub_reports(db, sort=sort, limit=limit, viewer_user_id=viewer)
    return {"reports": reports, "count": len(reports)}


@router.post("/reports/{petition_id}/upvote")
async def upvote_report(petition_id: str, user: dict | None = Depends(get_optional_user)):
    viewer = _viewer_id(user)
    if not viewer and not settings.google_auth_enabled:
        viewer = "demo-local"
    if not viewer:
        raise HTTPException(401, "Sign in to upvote reports")
    db = get_db()
    try:
        result = await toggle_upvote(db, petition_id, viewer)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return result
