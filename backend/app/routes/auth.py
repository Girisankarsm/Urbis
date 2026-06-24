from authlib.integrations.starlette_client import OAuth
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, user_profile
from app.services.session import COOKIE_NAME, SESSION_DAYS, create_session_token
from app.services.users import upsert_google_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.send",
        "prompt": "consent",
        "access_type": "offline",
    },
)


def _auth_enabled() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


@router.get("/status")
async def auth_status():
    return {
        "google_auth_enabled": _auth_enabled(),
        "login_url": "/api/auth/google" if _auth_enabled() else None,
    }


@router.get("/google")
async def google_login(request: Request):
    if not _auth_enabled():
        raise HTTPException(503, "Google OAuth is not configured")
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    if not _auth_enabled():
        raise HTTPException(503, "Google OAuth is not configured")

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        logger.exception("Google OAuth callback failed")
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth_error=1",
            status_code=302,
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    db = get_db()
    user = await upsert_google_user(
        db,
        userinfo=userinfo,
        refresh_token=token.get("refresh_token"),
    )

    session_token = create_session_token(
        user_id=user["_id"],
        email=user.get("email", ""),
        name=user.get("name", ""),
    )

    response = RedirectResponse(url=f"{settings.frontend_url}/?signed_in=1")
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=SESSION_DAYS * 24 * 3600,
    )
    return response


@router.get("/me")
async def me(request: Request):
    user = await get_current_user(request)
    return user_profile(user)


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(COOKIE_NAME)
    return response
