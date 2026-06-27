"""Distance-decayed infrastructure severity scoring."""

from __future__ import annotations

import math
from typing import Any


def proximity_score(distance: float | None, weight: float, decay_constant: float) -> float:
    if distance is None or decay_constant <= 0:
        return 0.0
    if distance < 0:
        distance = 0.0
    return weight * math.exp(-distance / decay_constant)


def compute_infra_score(
    distances: dict[str, float | None],
    config: dict[str, Any],
) -> tuple[float, list[dict[str, Any]]]:
    categories_cfg = config.get("categories") or {}
    contributions: list[dict[str, Any]] = []

    for category, cat_cfg in categories_cfg.items():
        dist = distances.get(category)
        weight = float(cat_cfg.get("weight", 0))
        decay = float(cat_cfg.get("decayConstant", 1))
        score = proximity_score(dist, weight, decay)
        if score > 0 or dist is not None:
            contributions.append(
                {
                    "category": category,
                    "distance": dist,
                    "score": round(score, 4),
                }
            )

    contributions.sort(key=lambda c: c["score"], reverse=True)
    infra_score = sum(c["score"] for c in contributions)
    return infra_score, contributions


def compute_final_severity(
    base_severity: float,
    infra_score: float,
    config: dict[str, Any],
) -> tuple[int, float]:
    max_infra = float(config.get("maxInfraScore", 60))
    alpha = float(config.get("alpha", 0.4))
    normalized = min(infra_score / max_infra, 1.0) if max_infra > 0 else 0.0
    final = min(round(base_severity * (1 + alpha * normalized)), 100)
    return int(final), normalized


def severity_level(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 35:
        return "moderate"
    return "low"


def format_contribution_line(category: str, distance: float | None) -> str:
    label = category.replace("_", " ").title()
    if distance is None:
        return f"{label} nearby"
    return f"{label} {int(round(distance))}m away"


def generate_severity_explanation(
    *,
    final_severity: int,
    base_issue_description: str,
    contributions: list[dict[str, Any]],
    top_n: int = 4,
) -> str:
    lines = [
        f"Severity: {final_severity}/100",
        "Reason:",
        f"• {base_issue_description}",
    ]
    added = 0
    for item in contributions:
        if added >= top_n:
            break
        if item.get("score", 0) <= 0:
            continue
        lines.append(f"• {format_contribution_line(item['category'], item.get('distance'))}")
        added += 1
    return "\n".join(lines)


def distances_from_nearest(nearest: dict[str, dict[str, Any]]) -> dict[str, float | None]:
    return {
        category: (info.get("distance") if info else None)
        for category, info in nearest.items()
    }
