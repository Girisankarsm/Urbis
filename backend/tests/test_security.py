"""Tests for security upload validation."""

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.services.security import detect_image_type, sanitize_filename, validate_upload


def test_sanitize_filename():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("photo.jpg") == "photo.jpg"


def test_detect_jpeg_magic():
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert detect_image_type(jpeg, "image/jpeg") == "image/jpeg"


@pytest.mark.asyncio
async def test_validate_upload_rejects_empty():
    file = UploadFile(filename="x.jpg", file=None)
    with pytest.raises(HTTPException) as exc:
        await validate_upload(file, b"", 1024)
    assert exc.value.status_code == 400
