"""Production configuration validation — used at API startup and by deploy scripts."""

from __future__ import annotations

from app.config import settings


def validate_deploy_config() -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block production startup."""
    errors: list[str] = []
    warnings: list[str] = []

    if settings.is_production:
        if settings.session_secret == "change-me-in-production":
            errors.append("SESSION_SECRET must be set to a long random value in production")

        mongo = settings.mongodb_url.lower()
        if "localhost" in mongo or "127.0.0.1" in mongo:
            errors.append(
                "MONGODB_URL must point to MongoDB Atlas (or another hosted cluster) in production"
            )

        if not settings.frontend_url.startswith("https://"):
            warnings.append("FRONTEND_URL should use https:// in production (required for OAuth cookies)")

        if not settings.api_base_url.startswith("https://"):
            warnings.append("API_BASE_URL should use https:// for correct upload URLs in emails")

        if settings.google_auth_enabled:
            redirect = settings.google_redirect_uri
            if "localhost" in redirect or "127.0.0.1" in redirect:
                errors.append(
                    "GOOGLE_REDIRECT_URI must be your production API callback "
                    "(https://<api-host>/api/auth/google/callback)"
                )
            if not redirect.startswith("https://"):
                errors.append("GOOGLE_REDIRECT_URI must use https:// in production")

        if not settings.cloudinary_enabled:
            warnings.append(
                "Cloudinary is not configured — Render disk is ephemeral; uploaded images will not persist"
            )

        if settings.lemma_enabled:
            if not settings.lemma_refresh_token and not settings.lemma_token:
                errors.append(
                    "Lemma is partially configured — set LEMMA_REFRESH_TOKEN (recommended) or LEMMA_TOKEN"
                )
            if settings.lemma_refresh_token and settings.lemma_token:
                warnings.append(
                    "Both LEMMA_REFRESH_TOKEN and LEMMA_TOKEN are set — prefer refresh token only on hosted API"
                )

        if not settings.google_auth_enabled and not settings.smtp_host:
            warnings.append("Neither Google OAuth nor SMTP is configured — complaint emails cannot be sent")

    return errors, warnings
