"""Upload validation and security helpers."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # WEBP checked further below
]

_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    name = Path(filename or "photo.jpg").name
    return _SAFE_FILENAME_RE.sub("_", name)[:120] or "photo.jpg"


def detect_image_type(content: bytes, declared_type: str | None) -> str | None:
    if len(content) < 12:
        return None
    for sig, mime in MAGIC_SIGNATURES:
        if content.startswith(sig):
            if mime == "image/webp" and content[8:12] != b"WEBP":
                continue
            return mime
    return declared_type if declared_type in ALLOWED_IMAGE_TYPES else None


async def validate_upload(file: UploadFile, content: bytes, max_bytes: int) -> str:
    """Validate upload size, type, and magic bytes. Returns verified content type."""
    if len(content) == 0:
        raise HTTPException(400, "Empty file")
    if len(content) > max_bytes:
        raise HTTPException(400, f"Image must be under {max_bytes // (1024 * 1024)} MB")

    ext = Path(file.filename or "").suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File extension {ext} not allowed")

    verified_type = detect_image_type(content, file.content_type)
    if not verified_type or verified_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, WebP, and GIF images are allowed")

    return verified_type
