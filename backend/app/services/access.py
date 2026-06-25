"""Petition access control when Google OAuth is enabled."""

from fastapi import HTTPException

from app.config import settings


def assert_petition_access(petition: dict, user: dict | None) -> None:
    if not settings.google_auth_enabled:
        return
    if not user:
        raise HTTPException(status_code=401, detail="Sign in with Google to continue")
    owner_id = petition.get("reporter_user_id")
    if owner_id and owner_id != user["_id"]:
        raise HTTPException(status_code=403, detail="You do not have access to this petition")
