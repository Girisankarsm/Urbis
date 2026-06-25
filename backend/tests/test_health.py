import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Urbis"


@pytest.mark.asyncio
async def test_list_petitions_demo_mode(client: AsyncClient):
    response = await client.get("/api/petitions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
