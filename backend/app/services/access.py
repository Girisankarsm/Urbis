"""Petition access control when Google OAuth is enabled."""

from fastapi import HTTPException

from app.config import settings

PUBLIC_READ_STATUSES = frozenset({"submitted", "under_review", "resolved", "escalated"})


def is_public_petition(petition: dict) -> bool:
    return petition.get("status") in PUBLIC_READ_STATUSES


def is_petition_owner(petition: dict, user: dict | None) -> bool:
    if not user:
        return False
    owner_id = petition.get("reporter_user_id")
    user_id = user.get("_id") or user.get("id")
    return bool(owner_id and user_id and owner_id == user_id)


def assert_petition_access(petition: dict, user: dict | None) -> None:
    if not settings.google_auth_enabled:
        return
    if not user:
        raise HTTPException(status_code=401, detail="Sign in with Google to continue")
    if is_petition_owner(petition, user):
        return
    if is_public_petition(petition):
        return
    raise HTTPException(status_code=403, detail="You do not have access to this petition")
