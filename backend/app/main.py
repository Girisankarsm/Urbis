import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.deploy_checks import validate_deploy_config
from app.services.lemma_service import (
    is_lemma_available,
    start_lemma_token_refresh_loop,
    stop_lemma_token_refresh_loop,
    verify_lemma_api,
    warm_lemma_token,
)
from app.database import close_db, connect_db
from app.routes.hub import router as hub_router
from app.routes.infrastructure import router as infrastructure_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes.analytics import router as analytics_router
from app.routes.auth import router as auth_router
from app.routes.petitions import router as petitions_router
from app.routes.uploads import upload_router
from app.routes.vision import router as vision_router
from app.services.verified_authorities import list_verified_cities
from app.services.infrastructure.cache import ensure_overpass_cache_indexes
from app.services.mongodb_indexes import ensure_indexes
from app.services.petitions import seed_departments

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    deploy_errors, deploy_warnings = validate_deploy_config()
    for warning in deploy_warnings:
        logger.warning("Deploy config: %s", warning)
    if deploy_errors:
        message = "Production configuration invalid:\n- " + "\n- ".join(deploy_errors)
        if settings.is_production:
            raise RuntimeError(message)
        logger.warning(message)
    if settings.is_production and settings.google_auth_enabled:
        if settings.effective_cookie_samesite != "none" or not settings.effective_cookie_secure:
            logger.warning(
                "Production OAuth across separate domains requires COOKIE_SAMESITE=none and COOKIE_SECURE=true"
            )
    try:
        await connect_db()
    except Exception as exc:
        raise RuntimeError(f"MongoDB connection failed — check MONGODB_URL: {exc}") from exc
    from app.database import get_db

    await seed_departments(get_db())
    try:
        await ensure_indexes(get_db())
        await ensure_overpass_cache_indexes(get_db())
    except Exception as exc:
        logger.warning("MongoDB index creation failed: %s", exc)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    if settings.lemma_enabled:
        try:
            await warm_lemma_token()
            start_lemma_token_refresh_loop()
            logger.info("Lemma auto-refresh enabled")
        except Exception as exc:
            logger.warning("Lemma startup refresh failed (will retry on demand): %s", exc)
    yield
    await stop_lemma_token_refresh_loop()
    await close_db()


app = FastAPI(
    title="Urbis API",
    description="Citizen civic-issue reporting with Lemma agentic infrastructure",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.rate_limit_requests_per_minute,
    )

app.include_router(auth_router)
app.include_router(petitions_router)
app.include_router(upload_router)
app.include_router(vision_router)
app.include_router(analytics_router)
app.include_router(hub_router)
app.include_router(infrastructure_router)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health/live")
async def health_live():
    """Lightweight liveness probe for load balancers (no external calls)."""
    return {"status": "ok", "app": "Urbis"}


@app.get("/api/health")
async def health():
    lemma = await verify_lemma_api()
    lemma_ok = bool(lemma.get("token_valid") and lemma.get("api_reachable"))
    return {
        "status": "ok",
        "app": "Urbis",
        "environment": settings.environment,
        "lemma_connected": settings.lemma_enabled,
        "lemma_token_valid": lemma_ok,
        "lemma_token_type": lemma.get("token_type"),
        "lemma_expires_at": lemma.get("expires_at"),
        "lemma_status": "ok" if lemma_ok else lemma.get("reason", "Lemma not verified"),
        "smtp_configured": bool(settings.smtp_host),
        "email_mode": (
            "lemma_gmail_or_smtp"
            if lemma_ok
            else ("gmail" if settings.google_auth_enabled else "smtp" if settings.smtp_host else "log_only")
        ),
        "authority_lookup": "verified registry + regional fallback" + (" + lemma agents" if lemma_ok else ""),
        "google_auth_enabled": settings.google_auth_enabled,
        "cloudinary_configured": settings.cloudinary_enabled,
        "image_storage": "cloudinary" if settings.cloudinary_enabled else "local",
        "production_ready": settings.is_production,
        "demo_email_redirect": settings.use_demo_email_redirect,
        "authority_discovery_enabled": settings.authority_discovery_enabled,
        "vision_enabled": settings.vision_enabled,
        "rate_limit_enabled": settings.rate_limit_enabled,
    }


@app.get("/api/health/lemma")
async def lemma_health():
    return await verify_lemma_api()


@app.get("/api/authorities/verified")
async def verified_authorities():
    """Cities with source-backed contact channels in verified_authorities.json."""
    cities = list_verified_cities()
    return {"cities": cities, "count": len(cities)}


@app.get("/api/setup")
async def setup_status():
    missing = []
    if not settings.lemma_enabled:
        missing.append("Lemma: set LEMMA_TOKEN and LEMMA_POD_ID, then run lemma pods import ./pod/civic-lens")
    elif not is_lemma_available():
        missing.append("Lemma: session token expired — run `lemma auth login` and update LEMMA_TOKEN in .env")
    if not settings.smtp_host:
        missing.append("SMTP: set SMTP_HOST, SMTP_USER, SMTP_PASSWORD for real email delivery")
    return {
        "ready_for_full_demo": is_lemma_available() and bool(settings.smtp_host),
        "lemma_connected": settings.lemma_enabled,
        "lemma_token_valid": is_lemma_available(),
        "smtp_configured": bool(settings.smtp_host),
        "missing": missing,
        "lemma_setup": [
            "backend/.venv/bin/lemma auth login",
            "backend/.venv/bin/lemma pods create urbis --org <org>",
            "backend/.venv/bin/lemma pods import ./pod/civic-lens",
            "Set LEMMA_TOKEN, LEMMA_POD_ID, LEMMA_ORG_ID in .env",
            "docker compose up -d --force-recreate api",
        ],
    }
