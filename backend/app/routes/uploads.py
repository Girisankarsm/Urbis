import logging
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.config import settings
from app.dependencies import get_optional_user
from app.services import cloudinary_storage

logger = logging.getLogger(__name__)

upload_router = APIRouter(prefix="/api/uploads", tags=["uploads"])


async def _save_local(content: bytes, ext: str) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    filepath = upload_dir / filename
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    path = f"/uploads/{filename}"
    base = settings.api_base_url.rstrip("/")
    return f"{base}{path}"


@upload_router.post("")
async def upload_image(
    file: UploadFile = File(...),
    kind: str = Query("petitions", pattern="^(petitions|follow-up)$"),
    user: dict | None = Depends(get_optional_user),
):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image must be under 10 MB")

    ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
    upload_kind = "follow-ups" if kind == "follow-up" else "petitions"

    if settings.cloudinary_enabled:
        try:
            url = await cloudinary_storage.upload_image(content, kind=upload_kind)
            return {"url": url, "storage": "cloudinary"}
        except Exception as exc:
            logger.error("Cloudinary upload failed: %s", exc)
            raise HTTPException(
                502,
                "Photo upload failed. Cloudinary is required so authorities can view your image.",
            ) from exc

    url = await _save_local(content, ext)
    return {"url": url, "storage": "local", "filename": Path(url).name}
