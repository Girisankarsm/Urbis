"""Tests for vision classification helpers."""

from app.services.vision_classification import normalize_issue_type, _keyword_classify


def test_normalize_issue_type_aliases():
    assert normalize_issue_type("broken_streetlight") == "streetlight"
    assert normalize_issue_type("open_manhole") == "manhole"
    assert normalize_issue_type("Pothole") == "pothole"


def test_keyword_classify_pothole():
    result = _keyword_classify("Large pothole near the bus stop causing traffic hazard")
    assert result["issue_type"] == "pothole"
    assert result["confidence"] > 0.5
