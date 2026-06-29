from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import certifi

from app.config import settings

client: AsyncIOMotorClient | None = None
db: AsyncIOMotorDatabase | None = None


def _mongo_client_kwargs() -> dict:
    url = settings.mongodb_url
    if url.startswith("mongodb+srv://") or "mongodb.net" in url:
        return {"tlsCAFile": certifi.where()}
    return {}


async def connect_db() -> None:
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_url, **_mongo_client_kwargs())
    db = client[settings.mongodb_db]


async def close_db() -> None:
    if client:
        client.close()


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("Database not initialized")
    return db
