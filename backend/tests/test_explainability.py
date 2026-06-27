"""Tests for explainability helpers."""

from app.services.explainability import build_ai_explanations


def test_build_ai_explanations_includes_all_sections():
    result = build_ai_explanations(
        vision={"issue_type": "pothole", "confidence": 0.9, "reasoning": "Visible crater", "source": "keyword"},
        classification={
            "issue_type": "pothole",
            "department": "Roads Dept",
            "department_email": "roads@example.gov",
            "confidence": 0.85,
            "reasoning": "Registry match",
        },
        severity={"severity_score": 72, "severity_level": "high", "reasoning": "Near school", "factors": {}},
        authority_source="registry",
    )
    assert result["vision_classification"]["issue_type"] == "pothole"
    assert "registry" in result["authority_routing"]["explanation"]
    assert result["severity_analysis"]["severity_score"] == 72
