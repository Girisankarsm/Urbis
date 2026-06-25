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
    district: str = ""
    suburb: str = ""
    postcode: str = ""


def _first(*values: str | None) -> str:
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return ""


async def reverse_geocode(lat: float, lng: float) -> GeoArea:
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "addressdetails": 1,
        "zoom": 14,
    }
    headers = {"User-Agent": "Urbis-CivicApp/1.0 (civic complaint routing)"}

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
    suburb = _first(address.get("suburb"), address.get("neighbourhood"), address.get("quarter"))
    district = _first(
        address.get("state_district"),
        address.get("county"),
        address.get("city_district"),
    )
    city = _first(
        address.get("city"),
        address.get("town"),
        address.get("village"),
        suburb,
        district,
    )
    state = _first(address.get("state"), address.get("region"))
    country = _first(address.get("country"))
    municipality = _first(
        address.get("municipality"),
        address.get("city_district"),
        address.get("borough"),
        city,
        "Local Municipality",
    )
    postcode = _first(address.get("postcode"))

    return GeoArea(
        display_name=data.get("display_name", f"{lat}, {lng}"),
        city=city,
        district=district,
        suburb=suburb,
        state=state,
        country=country,
        municipality=municipality,
        postcode=postcode,
        lat=lat,
        lng=lng,
    )
