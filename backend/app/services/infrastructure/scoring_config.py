"""Load infrastructure scoring configuration."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import settings

_CONFIG_PATH = Path(__file__).resolve().parent / "infrastructure_scoring.json"


@lru_cache(maxsize=1)
def load_infrastructure_scoring_config() -> dict[str, Any]:
    data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    if settings.infrastructure_radius_m:
        data = {**data, "radiusMeters": settings.infrastructure_radius_m}
    if settings.infrastructure_alpha is not None:
        data = {**data, "alpha": settings.infrastructure_alpha}
    return data
