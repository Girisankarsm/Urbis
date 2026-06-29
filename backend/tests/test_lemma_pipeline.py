"""Lemma-first intake pipeline tests."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.authority_lookup import lookup_authority
from app.services.geocoding import GeoArea
from app.services.lemma_pipeline import run_lemma_intake


@pytest.mark.asyncio
async def test_run_lemma_intake_success_records_invocations():
    area = GeoArea(
        display_name="Vandalur",
        city="Chengalpattu",
        municipality="Chengalpattu",
        state="Tamil Nadu",
        country="India",
        lat=12.88,
        lng=80.08,
    )
    classification = lookup_authority(area, "garbage pile")

    with (
        patch(
            "app.services.lemma_pipeline.lemma_service.run_petition_pipeline_intake",
            new_callable=AsyncMock,
            return_value={"run_id": "wf-1", "pod_petition_id": "pod-1"},
        ),
        patch(
            "app.services.lemma_pipeline.lemma_service.run_create_petition_function",
            new_callable=AsyncMock,
            return_value={"petition_id": "pod-1"},
        ),
        patch(
            "app.services.lemma_pipeline.lemma_service.classify_with_lemma",
            new_callable=AsyncMock,
            return_value={
                "issue_type": "garbage",
                "department": "GCC Sanitation",
                "department_email": "seswm@chennaicorporation.gov.in",
                "confidence": 0.9,
                "reasoning": "Lemma routed to sanitation",
            },
        ),
        patch(
            "app.services.lemma_pipeline.lemma_service.draft_email_with_lemma",
            new_callable=AsyncMock,
            return_value={
                "subject": "Complaint",
                "body": "Body",
                "to_email": "seswm@chennaicorporation.gov.in",
            },
        ),
        patch("app.services.lemma_pipeline.merge_lemma_classification", return_value=classification),
        patch("app.services.lemma_pipeline.lemma_service.mark_lemma_path_active") as mark_active,
    ):
        result = await run_lemma_intake(
            petition_id="mongo-1",
            photo_url="https://example.com/photo.jpg",
            description="garbage",
            location={"address": "Vandalur", "lat": 12.88, "lng": 80.08},
            area=area,
        )

    assert result.success is True
    assert "workflow:petition-pipeline" in result.invocations
    assert "function:create_petition" in result.invocations
    assert "agent:issue-classifier" in result.invocations
    assert "agent:complaint-drafter" in result.invocations
    mark_active.assert_called_once()
