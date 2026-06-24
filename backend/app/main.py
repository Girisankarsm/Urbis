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
    title="CivicLens API",
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
        "lemma_connected": settings.lemma_enabled,
        "smtp_configured": bool(settings.smtp_host),
    }
