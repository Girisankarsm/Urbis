from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import close_db, connect_db
from app.routes.petitions import router as petitions_router
from app.routes.petitions import upload_router
from app.services.petitions import seed_departments


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(petitions_router)
app.include_router(upload_router)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "app": "Urbis",
        "lemma_connected": settings.lemma_enabled,
        "smtp_configured": bool(settings.smtp_host),
        "email_mode": (
            "lemma_gmail_or_smtp"
            if settings.lemma_enabled
            else ("smtp" if settings.smtp_host else "log_only")
        ),
        "authority_lookup": "geocoding + regional contacts" + (" + lemma agents" if settings.lemma_enabled else ""),
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
            "docker compose restart api",
        ],
    }
