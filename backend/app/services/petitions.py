from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.models import (
    ActivityEvent,
    ApprovalRequest,
    ClassificationResult,
    CreatePetitionRequest,
    EmailDraft,
    PetitionStatus,
    ResolutionVerdict,
)
from app.services.ai import check_resolution, classify_issue, draft_complaint_email, draft_escalation_email
from app.services.departments import DEPARTMENTS
from app.services.email import send_email


def _oid() -> str:
    return str(uuid4())


def _serialize(doc: dict[str, Any]) -> dict[str, Any]:
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    for key in ("created_at", "updated_at", "submitted_at", "resolved_at", "escalated_at", "timestamp"):
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = doc[key].isoformat()
    return doc


async def seed_departments(db: AsyncIOMotorDatabase) -> None:
    count = await db.departments.count_documents({})
    if count == 0:
        await db.departments.insert_many(DEPARTMENTS)


async def log_activity(
    db: AsyncIOMotorDatabase,
    petition_id: str,
    event_type: str,
    message: str,
    metadata: dict | None = None,
) -> None:
    await db.activity_log.insert_one(
        {
            "petition_id": petition_id,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }
    )


async def list_petitions(db: AsyncIOMotorDatabase, status: str | None = None) -> list[dict]:
    query: dict = {}
    if status:
        query["status"] = status
    cursor = db.petitions.find(query).sort("created_at", -1)
    return [_serialize(doc) async for doc in cursor]


async def get_petition(db: AsyncIOMotorDatabase, petition_id: str) -> dict | None:
    doc = await db.petitions.find_one({"_id": petition_id})
    if not doc:
        try:
            doc = await db.petitions.find_one({"_id": ObjectId(petition_id)})
        except Exception:
            doc = None
    return _serialize(doc) if doc else None


async def get_activity(db: AsyncIOMotorDatabase, petition_id: str) -> list[dict]:
    cursor = db.activity_log.find({"petition_id": petition_id}).sort("timestamp", 1)
    return [_serialize(doc) async for doc in cursor]


async def create_and_process_petition(db: AsyncIOMotorDatabase, req: CreatePetitionRequest) -> dict:
    now = datetime.now(timezone.utc)
    petition_id = _oid()

    doc = {
        "_id": petition_id,
        "photo_url": req.photo_url,
        "location": req.location.model_dump(),
        "description": req.description,
        "status": PetitionStatus.DRAFT.value,
        "created_at": now,
        "updated_at": now,
    }
    await db.petitions.insert_one(doc)
    await log_activity(db, petition_id, "created", "Petition created from citizen report")

    classification = classify_issue(req.description, req.location)
    await db.petitions.update_one(
        {"_id": petition_id},
        {
            "$set": {
                "issue_type": classification.issue_type,
                "department": classification.department,
                "department_email": classification.department_email,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    await log_activity(
        db,
        petition_id,
        "classified",
        classification.reasoning,
        classification.model_dump(),
    )

    draft = draft_complaint_email(
        classification.issue_type,
        classification.department,
        classification.department_email,
        req.location,
        req.description,
        req.photo_url,
    )
    await db.petitions.update_one(
        {"_id": petition_id},
        {
            "$set": {
                "complaint_email_subject": draft.subject,
                "complaint_email_draft": draft.body,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    await log_activity(db, petition_id, "drafted", "Complaint email drafted by AI")
    await log_activity(db, petition_id, "approval_pending", "Awaiting citizen approval")

    return (await get_petition(db, petition_id)) or {}


async def approve_and_send(db: AsyncIOMotorDatabase, petition_id: str, req: ApprovalRequest) -> dict:
    petition = await get_petition(db, petition_id)
    if not petition:
        raise ValueError("Petition not found")

    if not req.approved:
        await log_activity(db, petition_id, "status_changed", "Email rejected by citizen")
        return petition

    to_email = petition.get("department_email") or settings.demo_email_to
    sent = send_email(to_email, req.subject, req.body)
    now = datetime.now(timezone.utc)

    if req.is_escalation:
        updates = {
            "escalation_email_draft": req.body,
            "status": PetitionStatus.ESCALATED.value,
            "escalated_at": now,
            "updated_at": now,
        }
        event = "escalation_sent"
        msg = f"Escalation email {'sent' if sent else 'logged (demo)'} to {to_email}"
    else:
        updates = {
            "complaint_email_subject": req.subject,
            "complaint_email_draft": req.body,
            "status": PetitionStatus.SUBMITTED.value,
            "submitted_at": now,
            "updated_at": now,
        }
        event = "email_sent"
        msg = f"Complaint email {'sent' if sent else 'logged (demo)'} to {to_email}"

    await db.petitions.update_one({"_id": petition_id}, {"$set": updates})
    await log_activity(db, petition_id, event, msg, {"to": to_email, "smtp_sent": sent})

    return (await get_petition(db, petition_id)) or {}


async def upload_follow_up(
    db: AsyncIOMotorDatabase,
    petition_id: str,
    follow_up_photo_url: str,
) -> dict:
    petition = await get_petition(db, petition_id)
    if not petition:
        raise ValueError("Petition not found")

    await db.petitions.update_one(
        {"_id": petition_id},
        {"$set": {"follow_up_photo_url": follow_up_photo_url, "updated_at": datetime.now(timezone.utc)}},
    )
    await log_activity(db, petition_id, "follow_up_uploaded", "Citizen uploaded follow-up photo")

    verdict = check_resolution(
        petition.get("issue_type") or "other",
        petition.get("description", ""),
    )
    status = verdict.recommended_status
    updates: dict = {
        "resolution_verdict": verdict.model_dump(),
        "status": status,
        "updated_at": datetime.now(timezone.utc),
    }
    if status == "resolved":
        updates["resolved_at"] = datetime.now(timezone.utc)

    await db.petitions.update_one({"_id": petition_id}, {"$set": updates})
    await log_activity(
        db,
        petition_id,
        "resolution_checked",
        verdict.reasoning,
        verdict.model_dump(),
    )

    return (await get_petition(db, petition_id)) or {}


async def find_stale_for_escalation(db: AsyncIOMotorDatabase) -> dict | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.escalation_days)
    cursor = db.petitions.find(
        {
            "status": PetitionStatus.SUBMITTED.value,
            "submitted_at": {"$lte": cutoff},
            "escalation_email_draft": {"$exists": False},
        }
    ).sort("submitted_at", 1).limit(1)

    async for doc in cursor:
        return _serialize(doc)
    return None


async def prepare_escalation(db: AsyncIOMotorDatabase, petition_id: str | None = None) -> dict | None:
    petition = await get_petition(db, petition_id) if petition_id else await find_stale_for_escalation(db)
    if not petition:
        return None

    pid = petition["id"]
    draft = draft_escalation_email(petition)
    await db.petitions.update_one(
        {"_id": pid},
        {
            "$set": {
                "escalation_email_draft": draft.body,
                "status": PetitionStatus.UNDER_REVIEW.value,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    await log_activity(db, pid, "escalation_pending", "Escalation email drafted — awaiting approval")

    petition = await get_petition(db, pid)
    return {
        **(petition or {}),
        "escalation_subject": draft.subject,
        "escalation_body": draft.body,
        "escalation_to": draft.to_email,
    }
