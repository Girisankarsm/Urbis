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
    payload = {
        "google_auth_enabled": _auth_enabled(),
        "login_url": "/api/auth/google" if _auth_enabled() else None,
    }
    if settings.is_production and _auth_enabled():
        payload["oauth_production_notes"] = (
            "Publish the OAuth consent screen and add your production redirect URI "
            f"({settings.google_redirect_uri}). Gmail send scope requires Google verification for public users."
        )
    return payload


@router.get("/google")
async def google_login(request: Request):
    if not _auth_enabled():
        raise HTTPException(503, "Google OAuth is not configured")
    redirect_uri = settings.google_redirect_uri
    # Explicit consent + offline access so Google returns a refresh_token for Gmail send.
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )


@router.get("/google/callback")
async def google_callback(request: Request):
    if not _auth_enabled():
        raise HTTPException(503, "Google OAuth is not configured")

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.exception("Google OAuth callback failed")
        error = request.query_params.get("error", "unknown")
        return RedirectResponse(
            url=f"{settings.frontend_url}/?auth_error={error}",
            status_code=302,
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    refresh_token = token.get("refresh_token")
    if not refresh_token:
        logger.warning(
            "Google OAuth returned no refresh_token for %s — Gmail send will not work until reconnect",
            userinfo.get("email"),
        )

    db = get_db()
    user = await upsert_google_user(
        db,
        userinfo=userinfo,
        refresh_token=refresh_token,
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
        samesite=settings.effective_cookie_samesite,
        secure=settings.effective_cookie_secure,
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )
    return response


@router.get("/me")
async def me(request: Request):
    user = await get_current_user(request)
    return user_profile(user)


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(
        COOKIE_NAME,
        samesite=settings.effective_cookie_samesite,
        secure=settings.effective_cookie_secure,
        path="/",
    )
    return response
