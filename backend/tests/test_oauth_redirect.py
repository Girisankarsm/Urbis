from starlette.requests import Request

from app.config import settings
from app.services.oauth_redirect import allowed_oauth_redirect_uris, oauth_redirect_uri


def _request(*, forwarded_host: str = "", forwarded_proto: str = "https") -> Request:
    scope = {
        "type": "http",
        "headers": [
            (b"x-forwarded-host", forwarded_host.encode()),
            (b"x-forwarded-proto", forwarded_proto.encode()),
        ],
    }
    return Request(scope)


def test_oauth_redirect_uses_forwarded_host_when_frontend_matches(monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://urbis-lemma.vercel.app")
    monkeypatch.setattr(
        settings,
        "google_redirect_uri",
        "https://urbis-ce0h.onrender.com/api/auth/google/callback",
    )
    monkeypatch.setattr(settings, "api_base_url", "https://urbis-ce0h.onrender.com")
    monkeypatch.setattr(settings, "cors_origins", "https://urbis-lemma.vercel.app")

    uri = oauth_redirect_uri(
        _request(forwarded_host="urbis-lemma.vercel.app", forwarded_proto="https"),
    )
    assert uri == "https://urbis-lemma.vercel.app/api/auth/google/callback"


def test_oauth_redirect_falls_back_to_configured_uri(monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://urbis-lemma.vercel.app")
    monkeypatch.setattr(
        settings,
        "google_redirect_uri",
        "https://urbis-ce0h.onrender.com/api/auth/google/callback",
    )
    monkeypatch.setattr(settings, "api_base_url", "https://urbis-ce0h.onrender.com")
    monkeypatch.setattr(settings, "cors_origins", "")

    uri = oauth_redirect_uri(_request())
    assert uri == "https://urbis-ce0h.onrender.com/api/auth/google/callback"


def test_allowed_oauth_redirect_uris_includes_frontend_and_api(monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://urbis-lemma.vercel.app")
    monkeypatch.setattr(
        settings,
        "google_redirect_uri",
        "https://urbis-ce0h.onrender.com/api/auth/google/callback",
    )
    monkeypatch.setattr(settings, "api_base_url", "https://urbis-ce0h.onrender.com")
    monkeypatch.setattr(settings, "cors_origins", "")

    allowed = allowed_oauth_redirect_uris()
    assert "https://urbis-lemma.vercel.app/api/auth/google/callback" in allowed
    assert "https://urbis-ce0h.onrender.com/api/auth/google/callback" in allowed
