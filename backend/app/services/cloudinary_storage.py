import asyncio
import logging
from io import BytesIO

import cloudinary
import cloudinary.uploader

from app.config import settings

logger = logging.getLogger(__name__)


def _configure() -> None:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def _upload_sync(content: bytes, *, folder: str) -> str:
    _configure()
    result = cloudinary.uploader.upload(
        BytesIO(content),
        folder=folder,
        resource_type="image",
    )
    return str(result["secure_url"])


async def upload_image(content: bytes, *, kind: str = "petitions") -> str:
    folder = f"{settings.cloudinary_folder}/{kind}".strip("/")
    return await asyncio.to_thread(_upload_sync, content, folder=folder)
