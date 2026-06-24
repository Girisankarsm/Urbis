"""Reverse geocode coordinates to municipality / area using OpenStreetMap Nominatim."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


@dataclass
class GeoArea:
    display_name: str
    city: str
    state: str
    country: str
    municipality: str
    lat: float
    lng: float


async def reverse_geocode(lat: float, lng: float) -> GeoArea:
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "addressdetails": 1,
        "zoom": 14,
    }
    headers = {"User-Agent": "Urbis-CivicApp/1.0 (hackathon demo)"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(NOMINATIM_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Geocoding failed: %s", exc)
        return GeoArea(
            display_name=f"{lat:.5f}, {lng:.5f}",
            city="",
            state="",
            country="",
            municipality="Local Municipality",
            lat=lat,
            lng=lng,
        )

    address = data.get("address") or {}
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("suburb")
        or address.get("county")
        or ""
    )
    state = address.get("state") or address.get("region") or ""
    country = address.get("country") or ""
    municipality = (
        address.get("municipality")
        or address.get("city_district")
        or address.get("borough")
        or city
        or "Local Municipality"
    )

    return GeoArea(
        display_name=data.get("display_name", f"{lat}, {lng}"),
        city=city,
        state=state,
        country=country,
        municipality=municipality,
        lat=lat,
        lng=lng,
    )
