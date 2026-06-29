"""Community hub tests."""

from datetime import datetime, timezone

import pytest

from app.services.hub import list_hub_reports, toggle_upvote


@pytest.mark.asyncio
async def test_hub_lists_public_reports_only(client):
    from app.database import get_db

    db = get_db()
    now = datetime.now(timezone.utc)
    await db.petitions.insert_one(
        {
            "_id": "hub-public-1",
            "status": "submitted",
            "issue_type": "garbage",
            "photo_url": "https://example.com/a.jpg",
            "description": "Trash on street",
            "location": {"lat": 12.9, "lng": 80.0, "address": "Test"},
            "area_info": {"display_name": "Test Area"},
            "reporter_name": "Alex",
            "upvote_count": 2,
            "created_at": now,
            "submitted_at": now,
        }
    )
    await db.petitions.insert_one(
        {
            "_id": "hub-draft-1",
            "status": "draft",
            "issue_type": "pothole",
            "photo_url": "https://example.com/b.jpg",
            "location": {"lat": 12.9, "lng": 80.0, "address": "Secret"},
            "created_at": now,
        }
    )

    reports = await list_hub_reports(db, sort="popular")
    ids = {r["id"] for r in reports}
    assert "hub-public-1" in ids
    assert "hub-draft-1" not in ids


@pytest.mark.asyncio
async def test_toggle_upvote(client):
    from app.database import get_db

    db = get_db()
    now = datetime.now(timezone.utc)
    await db.petitions.insert_one(
        {
            "_id": "hub-vote-1",
            "status": "submitted",
            "issue_type": "garbage",
            "photo_url": "https://example.com/c.jpg",
            "location": {"lat": 12.9, "lng": 80.0, "address": "Vote"},
            "upvote_count": 0,
            "created_at": now,
            "submitted_at": now,
        }
    )

    up = await toggle_upvote(db, "hub-vote-1", "user-a")
    assert up["upvoted_by_me"] is True
    assert up["upvote_count"] == 1

    down = await toggle_upvote(db, "hub-vote-1", "user-a")
    assert down["upvoted_by_me"] is False
    assert down["upvote_count"] == 0


@pytest.mark.asyncio
async def test_hub_api(client):
    response = await client.get("/api/hub/reports")
    assert response.status_code == 200
    assert "reports" in response.json()
