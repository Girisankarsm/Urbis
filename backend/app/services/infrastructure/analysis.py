"""Orchestrate nearby infrastructure fetch, scoring, and persistence fields."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.infrastructure.scoring_config import load_infrastructure_scoring_config
from app.services.infrastructure.cache import get_cached_overpass
from app.services.infrastructure.distance_utils import (
    map_display_markers,
    nearest_per_category,
)
from app.services.severity.infra_severity import (
    compute_final_severity,
    compute_infra_score,
    distances_from_nearest,
    generate_severity_explanation,
    severity_level,
)

logger = logging.getLogger(__name__)

_BASE_SEVERITY: dict[str, int] = {
    "pothole": 55,
    "garbage": 35,
    "streetlight": 40,
    "water_leak": 60,
    "fallen_tree": 75,
    "manhole": 85,
    "illegal_dumping": 45,
    "road_damage": 50,
    "sewage": 65,
    "other": 40,
}


def base_issue_severity(issue_type: str, description: str = "", vision_confidence: float = 0.5) -> float:
    base = float(_BASE_SEVERITY.get(issue_type, _BASE_SEVERITY["other"]))
    text = (description or "").lower()
    risk_words = ["danger", "accident", "injury", "children", "traffic", "blocked", "emergency"]
    risk_hits = sum(1 for w in risk_words if w in text)
    if risk_hits:
        base += min(10, risk_hits * 3)
    if vision_confidence >= 0.8 and issue_type in {"manhole", "fallen_tree", "water_leak"}:
        base += 5
    return min(base, 95.0)


def base_issue_description(issue_type: str, description: str = "") -> str:
    label = issue_type.replace("_", " ").title()
    if description.strip():
        return f"{label} reported — {description.strip()[:80]}"
    return f"{label} detected"


async def analyze_infrastructure(
    db: AsyncIOMotorDatabase,
    *,
    lat: float,
    lng: float,
    issue_type: str,
    description: str = "",
    vision_confidence: float = 0.5,
) -> dict[str, Any]:
    """Full infra-aware severity analysis. Never raises."""
    config = load_infrastructure_scoring_config()
    radius_m = int(config.get("radiusMeters", 500))
    base = base_issue_severity(issue_type, description, vision_confidence)

    try:
        overpass = await get_cached_overpass(db, lat, lng, radius_m)
    except Exception as exc:
        logger.warning("Infrastructure fetch failed lat=%s lng=%s: %s", lat, lng, exc)
        overpass = {"data": None, "source": "unavailable"}

    if overpass.get("data") is None:
        score = int(round(min(base, 100)))
        return {
            "severity_score": score,
            "severity_level": severity_level(score),
            "severity_explanation": generate_severity_explanation(
                final_severity=score,
                base_issue_description=base_issue_description(issue_type, description),
                contributions=[],
            ),
            "infrastructure": None,
            "factors": {"base_severity": base, "infra_unavailable": True},
            "map_markers": [],
        }

    nearest = nearest_per_category(overpass["data"], lat, lng)
    distances = distances_from_nearest(nearest)
    infra_score, contributions = compute_infra_score(distances, config)
    final_score, normalized_infra = compute_final_severity(base, infra_score, config)
    explanation = generate_severity_explanation(
        final_severity=final_score,
        base_issue_description=base_issue_description(issue_type, description),
        contributions=contributions,
    )

    school = nearest.get("school") or {}
    hospital = nearest.get("hospital") or {}
    bus = nearest.get("bus_stop") or {}
    gov = nearest.get("government_office") or {}
    metro = nearest.get("metro_station") or {}
    railway = nearest.get("railway_station") or {}
    station_dist = None
    if metro.get("distance") is not None and railway.get("distance") is not None:
        station_dist = min(metro["distance"], railway["distance"])
    elif metro.get("distance") is not None:
        station_dist = metro["distance"]
    elif railway.get("distance") is not None:
        station_dist = railway["distance"]

    infrastructure = {
        "distance_to_school": school.get("distance"),
        "distance_to_hospital": hospital.get("distance"),
        "distance_to_bus_stop": bus.get("distance"),
        "distance_to_station": station_dist,
        "distance_to_govt_office": gov.get("distance"),
        "nearest_school_name": school.get("name"),
        "nearest_hospital_name": hospital.get("name"),
        "infra_score": round(infra_score, 2),
        "contributions": contributions,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": overpass.get("source", "overpass"),
    }

    return {
        "severity_score": final_score,
        "severity_level": severity_level(final_score),
        "severity_explanation": explanation,
        "infrastructure": infrastructure,
        "map_markers": map_display_markers(nearest),
        "factors": {
            "base_severity": base,
            "infra_score": infra_score,
            "normalized_infra": normalized_infra,
            "alpha": config.get("alpha"),
        },
        "reasoning": explanation,
    }


async def fetch_map_infrastructure(
    db: AsyncIOMotorDatabase,
    *,
    lat: float,
    lng: float,
    radius_m: int | None = None,
) -> dict[str, Any]:
    """Public helper for map layer — never raises."""
    config = load_infrastructure_scoring_config()
    radius = radius_m or int(config.get("radiusMeters", 500))
    try:
        overpass = await get_cached_overpass(db, lat, lng, radius)
        if overpass.get("data") is None:
            return {"markers": [], "source": "unavailable"}
        nearest = nearest_per_category(overpass["data"], lat, lng)
        return {
            "markers": map_display_markers(nearest),
            "source": overpass.get("source", "overpass"),
        }
    except Exception as exc:
        logger.warning("Map infrastructure fetch failed: %s", exc)
        return {"markers": [], "source": "unavailable"}
