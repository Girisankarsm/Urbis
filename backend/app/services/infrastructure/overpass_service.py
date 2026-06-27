"""Overpass API fetch with mirror fallback."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

PRIMARY_ENDPOINT = "https://overpass-api.de/api/interpreter"
SECONDARY_ENDPOINT = "https://overpass.kumi.systems/api/interpreter"
TIMEOUT_SECONDS = 8.0


def build_combined_query(lat: float, lng: float, radius_m: int) -> str:
    return f"""
[out:json][timeout:8];
(
  node["amenity"="school"](around:{radius_m},{lat},{lng});
  way["amenity"="school"](around:{radius_m},{lat},{lng});
  node["amenity"="college"](around:{radius_m},{lat},{lng});
  way["amenity"="college"](around:{radius_m},{lat},{lng});
  node["amenity"="hospital"](around:{radius_m},{lat},{lng});
  way["amenity"="hospital"](around:{radius_m},{lat},{lng});
  node["amenity"="clinic"](around:{radius_m},{lat},{lng});
  way["amenity"="clinic"](around:{radius_m},{lat},{lng});
  node["highway"="bus_stop"](around:{radius_m},{lat},{lng});
  node["railway"="station"](around:{radius_m},{lat},{lng});
  way["railway"="station"](around:{radius_m},{lat},{lng});
  node["station"="subway"](around:{radius_m},{lat},{lng});
  way["station"="subway"](around:{radius_m},{lat},{lng});
  node["office"="government"](around:{radius_m},{lat},{lng});
  way["office"="government"](around:{radius_m},{lat},{lng});
  way["highway"~"^(primary|secondary|trunk)$"](around:{radius_m},{lat},{lng});
);
out center tags;
"""


async def _post_query(endpoint: str, query: str) -> list[dict[str, Any]] | None:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(endpoint, data={"data": query})
        if resp.status_code != 200:
            logger.warning("Overpass %s returned %s", endpoint, resp.status_code)
            return None
        payload = resp.json()
        elements = payload.get("elements", [])
        seen: dict[int, dict[str, Any]] = {}
        for el in elements:
            eid = el.get("id")
            if eid is not None:
                seen[int(eid)] = el
        return list(seen.values())
    except Exception as exc:
        logger.warning("Overpass request failed (%s): %s", endpoint, exc)
        return None


async def fetch_overpass_elements(lat: float, lng: float, radius_m: int) -> dict[str, Any]:
    """Fetch infrastructure elements; never raises."""
    query = build_combined_query(lat, lng, radius_m)
    elements = await _post_query(PRIMARY_ENDPOINT, query)
    source = "overpass"
    if elements is None:
        elements = await _post_query(SECONDARY_ENDPOINT, query)
        source = "overpass_mirror"
    if elements is None:
        logger.warning("Overpass unavailable for lat=%s lng=%s radius=%s", lat, lng, radius_m)
        return {"data": None, "source": "unavailable"}
    return {"data": elements, "source": source}
