from urllib.parse import urlparse

from starlette.requests import Request

from app.config import settings


def _callback_for_origin(origin: str) -> str:
    return f"{origin.rstrip('/')}/api/auth/google/callback"


def allowed_oauth_redirect_uris() -> set[str]:
    """Registered OAuth callback URLs (must match Google Cloud Console)."""
    allowed: set[str] = set()
    for value in (
        settings.google_redirect_uri,
        settings.frontend_url,
        settings.api_base_url,
        *settings.cors_origin_list,
    ):
        if not value:
            continue
        cleaned = value.strip().rstrip("/")
        if cleaned.endswith("/api/auth/google/callback"):
            allowed.add(cleaned)
            continue
        parsed = urlparse(cleaned)
        if parsed.scheme and parsed.netloc:
            allowed.add(_callback_for_origin(f"{parsed.scheme}://{parsed.netloc}"))
    return allowed


def oauth_redirect_uri(request: Request) -> str:
    """
    OAuth callback URL for this request.

    When the frontend proxies /api through Vercel, X-Forwarded-Host is the Vercel
    domain but GOOGLE_REDIRECT_URI may still point at Render. Using the forwarded
    host keeps the OAuth state cookie and Google redirect on the same site.
    """
    allowed = allowed_oauth_redirect_uris()
    forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "https").split(",")[0].strip()

    if forwarded_host:
        candidate = _callback_for_origin(f"{forwarded_proto}://{forwarded_host}")
        if candidate in allowed:
            return candidate
        frontend_host = urlparse(settings.frontend_url).netloc
        if forwarded_host == frontend_host:
            return candidate

    if settings.google_redirect_uri:
        return settings.google_redirect_uri.rstrip("/")
    return _callback_for_origin(settings.frontend_url)
