import pytest

from app.services.auth_codes import consume_auth_code, create_auth_code


@pytest.mark.asyncio
async def test_auth_code_roundtrip(test_db):
    code = await create_auth_code(test_db, user_id="user-123")
    assert len(code) > 20
    user_id = await consume_auth_code(test_db, code)
    assert user_id == "user-123"
    assert await consume_auth_code(test_db, code) is None


@pytest.mark.asyncio
async def test_auth_code_expires(test_db):
    from datetime import datetime, timedelta, timezone

    code = await create_auth_code(test_db, user_id="user-456")
    expired_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await test_db.auth_codes.update_one({"_id": code}, {"$set": {"expires_at": expired_at}})
    assert await consume_auth_code(test_db, code) is None
