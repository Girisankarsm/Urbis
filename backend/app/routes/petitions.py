import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models import ApprovalRequest, CreatePetitionRequest, FollowUpRequest
from app.services.petitions import (
    approve_and_send,
    create_and_process_petition,
    get_activity,
    get_petition,
    list_petitions,
    prepare_escalation,
    upload_follow_up,
)

router = APIRouter(prefix="/api/petitions", tags=["petitions"])


@router.get("")
async def get_petitions(
    status: str | None = Query(None),
    mine: bool = Query(False),
    user: dict | None = Depends(get_optional_user),
):
    db = get_db()
    if mine:
        if not user:
            raise HTTPException(401, "Sign in with Google to continue")
        return await list_petitions(db, status, reporter_user_id=user["_id"])
    return await list_petitions(db, status)


@router.get("/pending-approvals")
async def pending_approvals():
    db = get_db()
    drafts = await list_petitions(db, "draft")
    escalations = []
    for p in await list_petitions(db, "under_review"):
        if p.get("escalation_email_draft"):
            escalations.append(p)
    return {"complaints": drafts, "escalations": escalations}


@router.get("/{petition_id}")
async def get_one(petition_id: str):
    db = get_db()
    petition = await get_petition(db, petition_id)
    if not petition:
        raise HTTPException(404, "Petition not found")
    activity = await get_activity(db, petition_id)
    return {"petition": petition, "activity": activity}


@router.post("")
async def create_petition(req: CreatePetitionRequest, user: dict | None = Depends(get_optional_user)):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    db = get_db()
    petition = await create_and_process_petition(db, req, reporter=user)
    return {"petition": petition, "message": "Petition created — review the drafted email for approval"}


@router.post("/{petition_id}/approve")
async def approve_petition(
    petition_id: str,
    req: ApprovalRequest,
    user: dict | None = Depends(get_optional_user),
):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    db = get_db()
    try:
        petition = await approve_and_send(db, petition_id, req, sender=user)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    return {"petition": petition}


@router.post("/{petition_id}/follow-up")
async def follow_up(petition_id: str, req: FollowUpRequest):
    db = get_db()
    try:
        petition = await upload_follow_up(db, petition_id, req.follow_up_photo_url)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    return {"petition": petition}


@router.post("/escalation/check")
async def check_escalation():
    db = get_db()
    result = await prepare_escalation(db)
    if not result:
        return {"message": "No stale petitions found", "petition": None}
    return {"petition": result, "message": "Escalation draft ready for approval"}


upload_router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@upload_router.post("")
async def upload_image(file: UploadFile = File(...), user: dict | None = Depends(get_optional_user)):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are allowed")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = upload_dir / filename

    content = await file.read()
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    url = f"/uploads/{filename}"
    return {"url": url, "filename": filename}
