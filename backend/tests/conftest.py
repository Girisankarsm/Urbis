import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB", "urbis_test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("GOOGLE_CLIENT_ID", "")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "")

from app.database import close_db, connect_db, get_db  # noqa: E402
from app.main import app  # noqa: E402


def _mongo_available() -> bool:
    try:
        import pymongo

        client = pymongo.MongoClient(os.environ["MONGODB_URL"], serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


requires_mongo = pytest.mark.skipif(not _mongo_available(), reason="MongoDB not available")


@pytest_asyncio.fixture
async def client():
    if not _mongo_available():
        pytest.skip("MongoDB not available")
    await connect_db()
    db = get_db()
    for collection in ("petitions", "activity_log", "users", "petition_upvotes"):
        await db[collection].delete_many({})
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await close_db()


@pytest_asyncio.fixture
async def oauth_client(monkeypatch):
    if not _mongo_available():
        pytest.skip("MongoDB not available")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")

    from app.config import settings

    settings.google_client_id = "test-client-id"
    settings.google_client_secret = "test-client-secret"

    await connect_db()
    db = get_db()
    for collection in ("petitions", "activity_log", "users", "petition_upvotes"):
        await db[collection].delete_many({})
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await close_db()
