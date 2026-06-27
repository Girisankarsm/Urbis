"""Unit tests for infrastructure severity scoring."""

import math

import pytest

from app.services.infrastructure.cache import cache_key
from app.services.infrastructure.distance_utils import classify_element
from app.services.severity.infra_severity import (
    compute_final_severity,
    proximity_score,
)

SCORING_CONFIG = {
    "alpha": 0.4,
    "maxInfraScore": 60,
    "categories": {
        "school": {"weight": 20, "decayConstant": 150},
        "hospital": {"weight": 25, "decayConstant": 180},
    },
}


def test_proximity_score_at_zero_is_full_weight():
    assert proximity_score(0, 20, 150) == pytest.approx(20.0)


def test_proximity_score_at_decay_constant_is_about_37_percent():
    score = proximity_score(150, 20, 150)
    assert score == pytest.approx(20 * math.exp(-1), rel=1e-3)


def test_proximity_score_null_distance_is_zero():
    assert proximity_score(None, 20, 150) == 0.0


def test_compute_final_severity_low_base_cannot_hit_max_from_infra_alone():
    max_infra = 60.0
    final, _ = compute_final_severity(5, max_infra, SCORING_CONFIG)
    assert final < 50
    assert final < 100


def test_classify_element_school():
    assert classify_element({"amenity": "school"}) == "school"


def test_classify_element_metro():
    assert classify_element({"station": "subway"}) == "metro_station"


def test_classify_element_major_road():
    assert classify_element({"highway": "primary"}) == "major_road"


def test_cache_key_rounds_coordinates():
    assert cache_key(12.97161234, 77.59462345, 500) == "overpass:12.9716:77.5946:500"


@pytest.mark.asyncio
async def test_overpass_failure_returns_unavailable(monkeypatch):
    from app.services.infrastructure import overpass_service

    async def fail(*_args, **_kwargs):
        return None

    monkeypatch.setattr(overpass_service, "_post_query", fail)
    result = await overpass_service.fetch_overpass_elements(12.97, 77.59, 500)
    assert result["data"] is None
    assert result["source"] == "unavailable"
