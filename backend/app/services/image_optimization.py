"""Image optimization before storage."""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

MAX_DIMENSION = 1920
JPEG_QUALITY = 85


def optimize_image(content: bytes, content_type: str = "image/jpeg") -> tuple[bytes, str]:
    """Resize and compress images. Returns (bytes, content_type). Falls back to original on error."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        img = _apply_exif_orientation(img)

        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        fmt = "JPEG"
        out_type = "image/jpeg"
        if content_type == "image/png" and img.mode in ("RGBA", "LA"):
            fmt = "PNG"
            out_type = "image/png"
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        buf = io.BytesIO()
        if fmt == "PNG":
            img.save(buf, format="PNG", optimize=True)
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
            out_type = "image/jpeg"

        optimized = buf.getvalue()
        if len(optimized) < len(content):
            return optimized, out_type
        return content, content_type
    except Exception as exc:
        logger.debug("Image optimization skipped: %s", exc)
        return content, content_type


def _apply_exif_orientation(img):  # noqa: ANN001
    try:
        from PIL import ImageOps

        return ImageOps.exif_transpose(img)
    except Exception:
        return img
