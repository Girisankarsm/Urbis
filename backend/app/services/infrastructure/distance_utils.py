"""Haversine distance and Overpass element classification."""

from __future__ import annotations

import math
import re
from typing import Any

EARTH_RADIUS_M = 6_371_000.0

MAJOR_ROAD_RE = re.compile(r"^(primary|secondary|trunk)$")


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def element_lat_lng(element: dict[str, Any]) -> tuple[float, float] | None:
    if element.get("type") == "node":
        if "lat" in element and "lon" in element:
            return float(element["lat"]), float(element["lon"])
        return None
    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None


def classify_element(tags: dict[str, Any]) -> str | None:
    amenity = tags.get("amenity", "")
    highway = tags.get("highway", "")
    office = tags.get("office", "")
    railway = tags.get("railway", "")
    station = tags.get("station", "")

    if amenity == "school":
        return "school"
    if amenity == "college":
        return "school"
    if amenity == "hospital":
        return "hospital"
    if amenity == "clinic":
        return "clinic"
    if highway == "bus_stop":
        return "bus_stop"
    if station == "subway" or tags.get("subway") == "yes":
        return "metro_station"
    if railway in {"station", "halt", "stop"}:
        return "railway_station"
    if railway == "station" or tags.get("public_transport") == "station":
        if station == "subway":
            return "metro_station"
        return "railway_station"
    if office == "government":
        return "government_office"
    if highway and MAJOR_ROAD_RE.match(highway):
        return "major_road"
    return None


def nearest_per_category(
    elements: list[dict[str, Any]],
    lat: float,
    lng: float,
) -> dict[str, dict[str, Any]]:
    """Return nearest distance + name per scoring category."""
    categories = [
        "school",
        "hospital",
        "clinic",
        "bus_stop",
        "metro_station",
        "railway_station",
        "government_office",
        "major_road",
    ]
    nearest: dict[str, dict[str, Any]] = {
        cat: {"distance": None, "name": None, "lat": None, "lng": None}
        for cat in categories
    }

    for element in elements:
        tags = element.get("tags") or {}
        category = classify_element(tags)
        if not category:
            continue
        coords = element_lat_lng(element)
        if not coords:
            continue
        elat, elng = coords
        distance = haversine_meters(lat, lng, elat, elng)
        current = nearest[category]["distance"]
        if current is None or distance < current:
            name = (
                tags.get("name")
                or tags.get("operator")
                or tags.get("ref")
                or None
            )
            nearest[category] = {
                "distance": round(distance, 1),
                "name": name,
                "lat": elat,
                "lng": elng,
            }

    return nearest


def map_display_markers(nearest: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Markers for map: school, hospital, bus_stop, station (metro+rail merged)."""
    markers: list[dict[str, Any]] = []
    icon_map = {
        "school": "school",
        "hospital": "hospital",
        "bus_stop": "bus_stop",
    }

    for cat, icon in icon_map.items():
        info = nearest.get(cat) or {}
        if info.get("lat") is None:
            continue
        markers.append(
            {
                "category": cat,
                "icon": icon,
                "lat": info["lat"],
                "lng": info["lng"],
                "name": info.get("name"),
                "distance_m": info.get("distance"),
            }
        )

    station_candidates = []
    for cat in ("metro_station", "railway_station"):
        info = nearest.get(cat) or {}
        if info.get("lat") is not None and info.get("distance") is not None:
            station_candidates.append((info["distance"], info, cat))
    if station_candidates:
        station_candidates.sort(key=lambda x: x[0])
        _, info, cat = station_candidates[0]
        markers.append(
            {
                "category": "station",
                "icon": "station",
                "subtype": cat,
                "lat": info["lat"],
                "lng": info["lng"],
                "name": info.get("name"),
                "distance_m": info.get("distance"),
            }
        )

    return markers
