"""Lemma-first civic intake — pod workflows, agents, and functions before local fallback."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from app.config import settings
from app.models import EmailDraft
from app.services import lemma_service
from app.services.authority_lookup import merge_lemma_classification
from app.services.geocoding import GeoArea

logger = logging.getLogger(__name__)


@dataclass
class LemmaIntakeResult:
    success: bool
    classification: Any | None = None
    draft: EmailDraft | None = None
    authority_source: str = "lemma"
    pod_petition_id: str | None = None
    workflow_run_id: str | None = None
    invocations: list[str] = field(default_factory=list)
    error: str | None = None


async def run_lemma_intake(
    *,
    petition_id: str,
    photo_url: str,
    description: str,
    location: dict[str, Any],
    area: GeoArea,
) -> LemmaIntakeResult:
    """Run civic-lens pod resources in workflow order; return None fields on total failure."""
    invocations: list[str] = []
    pod_petition_id: str | None = None
    workflow_run_id: str | None = None

    intake = {
        "photo_url": photo_url,
        "description": description or "",
        "address": location.get("address") or area.display_name,
        "lat": float(location["lat"]),
        "lng": float(location["lng"]),
    }

    try:
        wf = await asyncio.wait_for(
            lemma_service.run_petition_pipeline_intake(intake),
            timeout=settings.lemma_pipeline_timeout_seconds,
        )
        workflow_run_id = wf.get("run_id")
        pod_petition_id = wf.get("pod_petition_id")
        if workflow_run_id:
            invocations.append("workflow:petition-pipeline")
    except Exception as exc:
        logger.warning("[fallback] Lemma petition-pipeline workflow failed: %s", exc)

    try:
        created = await asyncio.wait_for(
            lemma_service.run_create_petition_function(
                petition_id=petition_id,
                photo_url=photo_url,
                description=description,
                address=intake["address"],
                lat=intake["lat"],
                lng=intake["lng"],
                workflow_run_id=workflow_run_id,
            ),
            timeout=settings.lemma_pipeline_timeout_seconds,
        )
        pod_petition_id = str(created.get("petition_id") or pod_petition_id or "")
        invocations.append("function:create_petition")
    except Exception as exc:
        logger.warning("[fallback] Lemma create_petition function failed: %s", exc)

    pod_target = pod_petition_id or petition_id

    try:
        lemma_class = await asyncio.wait_for(
            lemma_service.classify_with_lemma(
                petition_id=pod_target,
                photo_url=photo_url,
                description=description,
                lat=intake["lat"],
                lng=intake["lng"],
                address=intake["address"],
                area_display=area.display_name,
                city=area.city,
                municipality=area.municipality,
                district=area.district,
                suburb=area.suburb,
                state=area.state,
                country=area.country,
            ),
            timeout=settings.lemma_pipeline_timeout_seconds,
        )
        invocations.append("agent:issue-classifier")
        classification = merge_lemma_classification(lemma_class, area, description)
    except Exception as exc:
        return LemmaIntakeResult(
            success=False,
            pod_petition_id=pod_petition_id,
            workflow_run_id=workflow_run_id,
            invocations=invocations,
            error=f"classification failed: {exc}",
        )

    try:
        lemma_draft = await asyncio.wait_for(
            lemma_service.draft_email_with_lemma(petition_id=pod_target),
            timeout=settings.lemma_pipeline_timeout_seconds,
        )
        invocations.append("agent:complaint-drafter")
        if not lemma_draft.get("subject") or not lemma_draft.get("body"):
            raise ValueError("Lemma drafter returned empty subject/body")
        draft = EmailDraft(
            subject=str(lemma_draft["subject"]),
            body=str(lemma_draft["body"]),
            to_email=str(lemma_draft.get("to_email") or classification.department_email or ""),
        )
    except Exception as exc:
        return LemmaIntakeResult(
            success=False,
            classification=classification,
            authority_source="lemma",
            pod_petition_id=pod_petition_id,
            workflow_run_id=workflow_run_id,
            invocations=invocations,
            error=f"draft failed: {exc}",
        )

    lemma_service.mark_lemma_path_active(invocations)

    return LemmaIntakeResult(
        success=True,
        classification=classification,
        draft=draft,
        authority_source="lemma",
        pod_petition_id=pod_petition_id,
        workflow_run_id=workflow_run_id,
        invocations=invocations,
    )
