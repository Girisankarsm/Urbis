from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.database import get_db
from app.services.session import COOKIE_NAME, create_session_token


async def _seed_petition(*, petition_id: str, reporter_user_id: str | None = None) -> str:
    db = get_db()
    doc = {
        "_id": petition_id,
        "photo_url": "https://example.com/a.jpg",
        "location": {"address": "Test", "lat": 12.97, "lng": 77.59},
        "description": "pothole on road",
        "status": "draft",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    if reporter_user_id:
        doc["reporter_user_id"] = reporter_user_id
    await db.petitions.insert_one(doc)
    return petition_id


@pytest.mark.asyncio
async def test_oauth_mode_requires_auth_for_petitions(oauth_client: AsyncClient):
    await _seed_petition(petition_id="petition-a", reporter_user_id="user-1")
    response = await oauth_client.get("/api/petitions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_oauth_mode_scopes_petitions_to_user(oauth_client: AsyncClient):
    db = get_db()
    await db.users.insert_one({"_id": "user-1", "email": "a@example.com", "name": "A"})
    await _seed_petition(petition_id="petition-a", reporter_user_id="user-1")
    await _seed_petition(petition_id="petition-b", reporter_user_id="user-2")

    token = create_session_token(user_id="user-1", email="a@example.com", name="A")
    response = await oauth_client.get("/api/petitions", cookies={COOKIE_NAME: token})
    assert response.status_code == 200
    ids = {p["id"] for p in response.json()}
    assert ids == {"petition-a"}


@pytest.mark.asyncio
async def test_oauth_mode_blocks_other_users_petition(oauth_client: AsyncClient):
    db = get_db()
    await db.users.insert_one({"_id": "user-1", "email": "a@example.com", "name": "A"})
    await _seed_petition(petition_id="petition-b", reporter_user_id="user-2")

    token = create_session_token(user_id="user-1", email="a@example.com", name="A")
    response = await oauth_client.get("/api/petitions/petition-b", cookies={COOKIE_NAME: token})
    assert response.status_code == 403
