from fastapi import HTTPException, Request

from app.config import settings
from app.database import get_db
from app.services.session import COOKIE_NAME, decode_session_token
from app.services.users import get_user_by_id, public_user


async def get_current_user(request: Request) -> dict:
    if not settings.google_auth_enabled:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured")
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Sign in with Google to continue")

    payload = decode_session_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")

    db = get_db()
    user = await get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_optional_user(request: Request) -> dict | None:
    if not settings.google_auth_enabled:
        return None
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    payload = decode_session_token(token)
    if not payload:
        return None
    db = get_db()
    user = await get_user_by_id(db, payload["sub"])
    return user


def user_profile(user: dict) -> dict:
    return public_user(user)
