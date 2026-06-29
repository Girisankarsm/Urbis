"""Verified municipal contact channels — email, portal, or helpline with source URLs."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models import ClassificationResult
from app.services.geocoding import GeoArea

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "verified_authorities.json"
VALID_CHANNELS = frozenset({"email", "portal", "helpline", "cpgrams"})


@lru_cache(maxsize=1)
def _load_data() -> dict[str, Any]:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return raw


def _area_haystack(area: GeoArea) -> str:
    parts = (
        area.display_name,
        area.city,
        area.district,
        area.suburb,
        area.municipality,
        area.state,
        area.country,
        area.postcode,
    )
    return " ".join(p for p in parts if p).lower()


def resolve_verified_city_key(area: GeoArea) -> str | None:
    """Match a verified city entry by name or suburb alias."""
    haystack = _area_haystack(area)
    cities: dict[str, Any] = _load_data().get("cities", {})

    for key in sorted(cities.keys(), key=len, reverse=True):
        if key in haystack:
            return key

    for key, entry in cities.items():
        for alias in entry.get("aliases", []):
            if alias.lower() in haystack:
                return key
    return None


def _entry_to_classification(
    issue: str,
    entry: dict[str, Any],
    *,
    city_key: str,
    match_kind: str,
    label: str,
    area: GeoArea,
) -> ClassificationResult:
    channel = str(entry.get("channel_type", "email")).lower()
    value = str(entry.get("value", "")).strip()
    department = str(entry.get("department_name", "Municipal Authority"))
    source_url = str(entry.get("source_url", "")).strip()

    if channel not in VALID_CHANNELS:
        channel = "email"

    email = value if channel == "email" else ""

    return ClassificationResult(
        issue_type=issue,
        department=department,
        department_email=email,
        contact_channel=channel,
        contact_value=value,
        source_url=source_url,
        confidence=0.95 if match_kind == "city" else 0.9,
        reasoning=(
            f"Located complaint in {label}, {area.state or area.country}. "
            f"Matched verified contact for {city_key} ({channel}) with published source."
        ),
        authority_source="verified",
    )


def lookup_verified_authority(
    area: GeoArea,
    description: str,
    issue_type: str,
) -> ClassificationResult | None:
    city_key = resolve_verified_city_key(area)
    if not city_key:
        return None

    data = _load_data()
    city_entry = data.get("cities", {}).get(city_key, {})
    issues: dict[str, Any] = city_entry.get("issues", {})

    issue_entry = issues.get(issue_type) or issues.get("other")
    if not issue_entry:
        fallback = city_entry.get("city_fallback")
        if fallback:
            issue_entry = fallback
        else:
            return None

    label = (
        area.city
        or area.suburb
        or area.district
        or area.municipality
        or area.display_name.split(",")[0]
        or "your area"
    )

    haystack = _area_haystack(area)
    match_kind = "city" if city_key in haystack else "metro"
    return _entry_to_classification(
        issue_type,
        issue_entry,
        city_key=city_key,
        match_kind=match_kind,
        label=label,
        area=area,
    )


def national_fallback_classification(issue_type: str, area: GeoArea) -> ClassificationResult:
    """CPGRAMS when no local verified or registry contact exists."""
    fb = _load_data().get("national_fallback", {})
    label = area.city or area.district or area.display_name.split(",")[0] or "your area"
    channel = str(fb.get("channel_type", "portal"))
    value = str(fb.get("value", "https://pgportal.gov.in"))
    return ClassificationResult(
        issue_type=issue_type,
        department=str(fb.get("department_name", "CPGRAMS")),
        department_email="",
        contact_channel=channel,
        contact_value=value,
        source_url=str(fb.get("source_url", value)),
        confidence=0.5,
        reasoning=(
            f"No verified local contact for {label}, {area.state or area.country}. "
            "Falling back to national CPGRAMS portal."
        ),
        authority_source="cpgrams",
    )


def list_verified_cities() -> list[str]:
    return sorted(_load_data().get("cities", {}).keys())
