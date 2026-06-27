from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.dependencies import get_optional_user
from app.models import ClassifyVisionRequest
from app.services.vision_classification import VISION_ISSUE_TYPES, classify_image

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.post("/classify")
async def classify_vision(
    req: ClassifyVisionRequest,
    user: dict | None = Depends(get_optional_user),
):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    if not settings.vision_enabled:
        raise HTTPException(503, "Vision classification is disabled")
    if not req.photo_url.strip():
        raise HTTPException(400, "photo_url is required")

    result = await classify_image(req.photo_url, description=req.description)
    return {
        "classification": result,
        "issue_types": VISION_ISSUE_TYPES,
    }
