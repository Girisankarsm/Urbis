"""AI explainability — store confidence, reasons, and authority selection context."""

from __future__ import annotations

from typing import Any


def build_ai_explanations(
    *,
    vision: dict[str, Any] | None = None,
    classification: dict[str, Any] | None = None,
    severity: dict[str, Any] | None = None,
    authority_source: str = "",
    user_override: str | None = None,
) -> dict[str, Any]:
    explanations: dict[str, Any] = {}

    if vision:
        explanations["vision_classification"] = {
            "issue_type": vision.get("issue_type"),
            "confidence": vision.get("confidence"),
            "reasoning": vision.get("reasoning"),
            "source": vision.get("source"),
            "user_override": user_override,
        }

    if classification:
        explanations["authority_routing"] = {
            "issue_type": classification.get("issue_type"),
            "department": classification.get("department"),
            "department_email": classification.get("department_email"),
            "confidence": classification.get("confidence"),
            "reasoning": classification.get("reasoning"),
            "authority_source": authority_source or classification.get("authority_source"),
            "explanation": _authority_explanation(authority_source, classification),
        }

    if severity:
        explanations["severity_analysis"] = {
            "severity_score": severity.get("severity_score"),
            "severity_level": severity.get("severity_level"),
            "reasoning": severity.get("severity_explanation") or severity.get("reasoning"),
            "factors": severity.get("factors", {}),
        }

    return explanations


def _authority_explanation(authority_source: str, classification: dict[str, Any]) -> str:
    dept = classification.get("department", "municipal authority")
    email = classification.get("department_email", "")
    source = authority_source or classification.get("authority_source", "registry")
    if source == "registry":
        return f"Routed to {dept} using verified regional municipal contact registry{f' ({email})' if email else ''}."
    if source == "web_search":
        return f"Discovered {dept} via web search for official government contact{f' ({email})' if email else ''}."
    if source == "lemma":
        return f"Lemma issue-classifier agent selected {dept} based on location and issue type{f' ({email})' if email else ''}."
    return f"Routed to {dept} using local classification rules."
