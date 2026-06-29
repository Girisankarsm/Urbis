from authlib.integrations.starlette_client import OAuth
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, user_profile
from app.services.auth_codes import consume_auth_code, create_auth_code
from app.services.auth_cookies import attach_session_cookie, clear_session_cookie
from app.services.oauth_redirect import oauth_redirect_uri
from app.services.session import SESSION_DAYS, create_session_token
from app.services.users import get_user_by_id, upsert_google_user

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


class AuthCompleteRequest(BaseModel):
    code: str = Field(min_length=16, max_length=128)


@router.get("/status")
async def auth_status(request: Request):
    payload = {
        "google_auth_enabled": _auth_enabled(),
        "login_url": "/api/auth/google" if _auth_enabled() else None,
    }
    if _auth_enabled():
        payload["oauth_redirect_uri"] = oauth_redirect_uri(request)
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
    redirect_uri = oauth_redirect_uri(request)
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
    except Exception:
        logger.exception("Google OAuth callback failed")
        error = request.query_params.get("error", "oauth_failed")
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

    auth_code = await create_auth_code(db, user_id=user["_id"])
    response = RedirectResponse(
        url=f"{settings.frontend_url}/?signed_in=1&auth_code={auth_code}",
    )
    attach_session_cookie(response, session_token)
    return response


@router.post("/complete")
async def complete_sign_in(body: AuthCompleteRequest):
    """
    Exchange a one-time post-OAuth code for a session cookie.

    Mobile Safari often drops cookies set on OAuth redirect responses; this POST
    sets the session cookie on a normal same-origin API response instead.
    """
    db = get_db()
    user_id = await consume_auth_code(db, body.code.strip())
    if not user_id:
        raise HTTPException(status_code=401, detail="Sign-in link expired — please try again")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    session_token = create_session_token(
        user_id=user["_id"],
        email=user.get("email", ""),
        name=user.get("name", ""),
    )
    response = JSONResponse(user_profile(user))
    attach_session_cookie(response, session_token)
    return response


@router.get("/me")
async def me(request: Request):
    user = await get_current_user(request)
    return user_profile(user)


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    clear_session_cookie(response)
    return response
