"""Severity scoring for civic issues (0–100)."""

from __future__ import annotations

import logging
import math
from typing import Any

import httpx

from app.config import settings

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


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


async def _nearby_pois(lat: float, lng: float, radius_m: int = 500) -> dict[str, int]:
    """Count schools and hospitals near coordinates via Overpass API."""
    query = f"""
    [out:json][timeout:8];
    (
      node["amenity"="school"](around:{radius_m},{lat},{lng});
      way["amenity"="school"](around:{radius_m},{lat},{lng});
      node["amenity"="hospital"](around:{radius_m},{lat},{lng});
      way["amenity"="hospital"](around:{radius_m},{lat},{lng});
      node["highway"="primary"](around:{radius_m},{lat},{lng});
      node["highway"="trunk"](around:{radius_m},{lat},{lng});
    );
    out center;
    """
    counts = {"schools": 0, "hospitals": 0, "major_roads": 0}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query},
            )
        if resp.status_code != 200:
            return counts
        elements = resp.json().get("elements", [])
        for el in elements:
            tags = el.get("tags") or {}
            amenity = tags.get("amenity", "")
            highway = tags.get("highway", "")
            if amenity == "school":
                counts["schools"] += 1
            elif amenity == "hospital":
                counts["hospitals"] += 1
            elif highway in {"primary", "trunk", "motorway"}:
                counts["major_roads"] += 1
    except Exception as exc:
        logger.debug("Overpass POI lookup failed: %s", exc)
    return counts


async def analyze_severity(
    *,
    issue_type: str,
    lat: float,
    lng: float,
    description: str = "",
    vision_confidence: float = 0.5,
) -> dict[str, Any]:
    """Compute severity score 0–100 with explanatory factors."""
    base = _BASE_SEVERITY.get(issue_type, _BASE_SEVERITY["other"])
    factors: dict[str, Any] = {"base_issue_type": base}

    pois = await _nearby_pois(lat, lng, radius_m=settings.severity_poi_radius_m)
    factors["nearby_schools"] = pois["schools"]
    factors["nearby_hospitals"] = pois["hospitals"]
    factors["nearby_major_roads"] = pois["major_roads"]

    score = float(base)

    if pois["schools"] > 0:
        boost = min(15, pois["schools"] * 5)
        score += boost
        factors["school_proximity_boost"] = boost

    if pois["hospitals"] > 0:
        boost = min(10, pois["hospitals"] * 4)
        score += boost
        factors["hospital_proximity_boost"] = boost

    if pois["major_roads"] > 0:
        boost = min(12, pois["major_roads"] * 3)
        score += boost
        factors["traffic_density_boost"] = boost

    text = (description or "").lower()
    risk_words = ["danger", "accident", "injury", "children", "traffic", "blocked", "emergency"]
    risk_hits = sum(1 for w in risk_words if w in text)
    if risk_hits:
        boost = min(10, risk_hits * 3)
        score += boost
        factors["pedestrian_risk_boost"] = boost

    if vision_confidence >= 0.8 and issue_type in {"manhole", "fallen_tree", "water_leak"}:
        score += 5
        factors["high_confidence_hazard_boost"] = 5

    score = int(round(min(100, max(0, score))))
    factors["final_score"] = score

    if score >= 75:
        level = "critical"
    elif score >= 55:
        level = "high"
    elif score >= 35:
        level = "moderate"
    else:
        level = "low"

    return {
        "severity_score": score,
        "severity_level": level,
        "factors": factors,
        "reasoning": (
            f"Severity {score}/100 ({level}): {issue_type.replace('_', ' ')} issue "
            f"with {pois['schools']} school(s), {pois['hospitals']} hospital(s), "
            f"and {pois['major_roads']} major road segment(s) within "
            f"{settings.severity_poi_radius_m}m."
        ),
    }
