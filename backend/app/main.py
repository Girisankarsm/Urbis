import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import close_db, connect_db
from app.routes.auth import router as auth_router
from app.routes.petitions import router as petitions_router
from app.routes.uploads import upload_router
from app.services.petitions import seed_departments

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.is_production and settings.session_secret == "change-me-in-production":
        raise RuntimeError("SESSION_SECRET must be set to a long random value in production")
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
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield
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

app.include_router(auth_router)
app.include_router(petitions_router)
app.include_router(upload_router)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": "Urbis",
        "environment": settings.environment,
        "lemma_connected": settings.lemma_enabled,
        "smtp_configured": bool(settings.smtp_host),
        "email_mode": (
            "lemma_gmail_or_smtp"
            if settings.lemma_enabled
            else ("smtp" if settings.smtp_host else "log_only")
        ),
        "authority_lookup": "geocoding + regional contacts" + (" + lemma agents" if settings.lemma_enabled else ""),
        "google_auth_enabled": settings.google_auth_enabled,
        "cloudinary_configured": settings.cloudinary_enabled,
        "image_storage": "cloudinary" if settings.cloudinary_enabled else "local",
        "production_ready": settings.is_production,
        "demo_email_redirect": settings.use_demo_email_redirect,
        "authority_discovery_enabled": settings.authority_discovery_enabled,
    }


@app.get("/api/setup")
async def setup_status():
    missing = []
    if not settings.lemma_enabled:
        missing.append("Lemma: set LEMMA_TOKEN and LEMMA_POD_ID, then run lemma pods import ./pod/civic-lens")
    if not settings.smtp_host:
        missing.append("SMTP: set SMTP_HOST, SMTP_USER, SMTP_PASSWORD for real email delivery")
    return {
        "ready_for_full_demo": settings.lemma_enabled and bool(settings.smtp_host),
        "lemma_connected": settings.lemma_enabled,
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
