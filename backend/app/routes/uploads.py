import logging
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.config import settings
from app.dependencies import get_optional_user
from app.services import cloudinary_storage
from app.services.image_optimization import optimize_image
from app.services.security import sanitize_filename, validate_upload

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

    content = await file.read()
    verified_type = await validate_upload(file, content, settings.upload_max_bytes)
    content, verified_type = optimize_image(content, verified_type)

    ext = Path(sanitize_filename(file.filename or "photo.jpg")).suffix or ".jpg"
    upload_kind = "follow-ups" if kind == "follow-up" else "petitions"

    if settings.cloudinary_enabled:
        try:
            url = await cloudinary_storage.upload_image(content, kind=upload_kind)
            return {"url": url, "storage": "cloudinary"}
        except Exception as exc:
            logger.error("Cloudinary upload failed: %s", exc)
            if settings.is_production:
                detail = (
                    "Photo upload failed. Check Cloudinary API key has Upload permission "
                    f"in the Cloudinary dashboard. ({exc})"
                )
                raise HTTPException(502, detail) from exc
            logger.warning("Falling back to local storage in development")
            url = await _save_local(content, ext)
            return {
                "url": url,
                "storage": "local",
                "warning": (
                    "Cloudinary upload failed (API key may lack Upload permission). "
                    "Using local storage for this session — fix Cloudinary for production."
                ),
            }

    url = await _save_local(content, ext)
    return {"url": url, "storage": "local", "filename": Path(url).name}
