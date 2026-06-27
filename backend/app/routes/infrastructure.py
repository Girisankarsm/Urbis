from fastapi import APIRouter, Query

from app.database import get_db
from app.services.infrastructure.analysis import fetch_map_infrastructure

router = APIRouter(prefix="/api/infrastructure", tags=["infrastructure"])


@router.get("/nearby")
async def nearby_infrastructure(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int | None = Query(None, ge=100, le=2000),
):
    db = get_db()
    return await fetch_map_infrastructure(db, lat=lat, lng=lng, radius_m=radius_m)
