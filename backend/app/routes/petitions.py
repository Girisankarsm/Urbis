from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import settings
from app.database import get_db
from app.dependencies import get_optional_user
from app.models import ApprovalRequest, CheckDuplicatesRequest, CreatePetitionRequest, FollowUpRequest
from app.services.access import assert_petition_access
from app.services.duplicate_detection import find_nearby_duplicates
from app.services.petitions import (
    approve_and_send,
    create_and_process_petition,
    delete_petition,
    get_activity,
    get_petition,
    list_petitions,
    prepare_escalation,
    upload_follow_up,
)

router = APIRouter(prefix="/api/petitions", tags=["petitions"])


def _user_filter(user: dict | None) -> str | None:
    if settings.google_auth_enabled:
        if not user:
            raise HTTPException(401, "Sign in with Google to continue")
        return user["_id"]
    return None


@router.get("")
async def get_petitions(
    status: str | None = Query(None),
    mine: bool = Query(False),
    user: dict | None = Depends(get_optional_user),
):
    db = get_db()
    reporter_id = _user_filter(user) if settings.google_auth_enabled or mine else None
    if mine and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    if mine and user:
        reporter_id = user["_id"]
    return await list_petitions(db, status, reporter_user_id=reporter_id)


@router.get("/pending-approvals")
async def pending_approvals(user: dict | None = Depends(get_optional_user)):
    db = get_db()
    reporter_id = _user_filter(user)
    drafts = await list_petitions(db, "draft", reporter_user_id=reporter_id)
    escalations = []
    for p in await list_petitions(db, "under_review", reporter_user_id=reporter_id):
        if p.get("escalation_email_draft"):
            escalations.append(p)
    return {"complaints": drafts, "escalations": escalations}


@router.post("/check-duplicates")
async def check_duplicates(
    req: CheckDuplicatesRequest,
    user: dict | None = Depends(get_optional_user),
):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    db = get_db()
    duplicates = await find_nearby_duplicates(
        db,
        lat=req.lat,
        lng=req.lng,
        issue_type=req.issue_type,
        photo_url=req.photo_url,
    )
    return {"duplicates": duplicates, "has_duplicates": len(duplicates) > 0}


@router.post("/escalation/check")
async def check_escalation(user: dict | None = Depends(get_optional_user)):
    db = get_db()
    reporter_id = _user_filter(user) if settings.google_auth_enabled else None
    result = await prepare_escalation(db, reporter_user_id=reporter_id)
    if not result:
        return {"message": "No stale petitions found", "petition": None}
    return {"petition": result, "message": "Escalation draft ready for approval"}


@router.get("/{petition_id}")
async def get_one(petition_id: str, user: dict | None = Depends(get_optional_user)):
    db = get_db()
    petition = await get_petition(db, petition_id)
    if not petition:
        raise HTTPException(404, "Petition not found")
    assert_petition_access(petition, user)
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
    petition = await get_petition(db, petition_id)
    if not petition:
        raise HTTPException(404, "Petition not found")
    assert_petition_access(petition, user)
    try:
        petition = await approve_and_send(db, petition_id, req, sender=user)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "petition": petition,
        "email_sent": petition.get("email_sent", False),
        "contact_filed": petition.get("contact_filed", False),
        "sent_to": petition.get("sent_to"),
        "intended_to": petition.get("intended_to"),
        "send_message": petition.get("send_message", ""),
    }


@router.delete("/{petition_id}")
async def remove_petition(petition_id: str, user: dict | None = Depends(get_optional_user)):
    if settings.google_auth_enabled and not user:
        raise HTTPException(401, "Sign in with Google to continue")
    db = get_db()
    petition = await get_petition(db, petition_id)
    if not petition:
        raise HTTPException(404, "Petition not found")
    assert_petition_access(petition, user)
    deleted = await delete_petition(db, petition_id)
    if not deleted:
        raise HTTPException(404, "Petition not found")
    return {"message": "Petition deleted", "id": petition_id}


@router.post("/{petition_id}/follow-up")
async def follow_up(
    petition_id: str,
    req: FollowUpRequest,
    user: dict | None = Depends(get_optional_user),
):
    db = get_db()
    petition = await get_petition(db, petition_id)
    if not petition:
        raise HTTPException(404, "Petition not found")
    assert_petition_access(petition, user)
    try:
        petition = await upload_follow_up(db, petition_id, req.follow_up_photo_url)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    return {"petition": petition}
