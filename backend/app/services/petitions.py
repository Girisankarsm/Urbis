import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.models import (
    ApprovalRequest,
    CreatePetitionRequest,
    EmailDraft,
    PetitionStatus,
    ResolutionVerdict,
)
from app.services import lemma_service
from app.services.ai import check_resolution, draft_complaint_email, draft_escalation_email
from app.services.authority_discovery import discover_with_timeout
from app.services.authority_lookup import lookup_authority
from app.services.departments import DEPARTMENTS
from app.services.email import send_email
from app.services.explainability import build_ai_explanations
from app.services.geocoding import reverse_geocode
from app.services.gmail import send_gmail_as_user
from app.services.lemma_pipeline import run_lemma_intake
from app.services.resolution_verification import verify_resolution
from app.services.severity_analysis import analyze_severity
from app.services.vision_classification import classify_image, normalize_issue_type

logger = logging.getLogger(__name__)


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


async def list_petitions(
    db: AsyncIOMotorDatabase,
    status: str | None = None,
    reporter_user_id: str | None = None,
) -> list[dict]:
    query: dict = {}
    if status:
        query["status"] = status
    if reporter_user_id:
        query["reporter_user_id"] = reporter_user_id
    cursor = db.petitions.find(query).sort("created_at", -1)
    return [_serialize(doc) async for doc in cursor]


async def get_petition(db: AsyncIOMotorDatabase, petition_id: str) -> dict | None:
    doc = await db.petitions.find_one({"_id": petition_id})
    if not doc:
        try:
            doc = await db.petitions.find_one({"_id": ObjectId(petition_id)})
        except Exception:
            doc = None
    if not doc:
        return None
    petition = _serialize(doc)
    pod_id = petition.get("lemma_pod_petition_id")
    if pod_id and lemma_service.is_lemma_available():
        pod_row = await lemma_service.fetch_pod_petition(str(pod_id))
        if pod_row:
            petition["lemma_pod_status"] = pod_row.get("status")
            petition["lemma_pod_synced_at"] = pod_row.get("updated_at") or pod_row.get("submitted_at")
    return petition


async def delete_petition(db: AsyncIOMotorDatabase, petition_id: str) -> bool:
    result = await db.petitions.delete_one({"_id": petition_id})
    if result.deleted_count == 0:
        try:
            result = await db.petitions.delete_one({"_id": ObjectId(petition_id)})
        except Exception:
            pass
    if result.deleted_count == 0:
        return False
    await db.activity_log.delete_many({"petition_id": petition_id})
    return True


async def get_activity(db: AsyncIOMotorDatabase, petition_id: str) -> list[dict]:
    cursor = db.activity_log.find({"petition_id": petition_id}).sort("timestamp", 1)
    local = [_serialize(doc) async for doc in cursor]
    petition = await get_petition(db, petition_id)
    pod_id = (petition or {}).get("lemma_pod_petition_id")
    if pod_id and lemma_service.is_lemma_available():
        pod_events = await lemma_service.fetch_pod_activity(str(pod_id))
        for event in pod_events:
            local.append(
                {
                    "id": f"lemma-{event.get('id', event.get('event_type', 'pod'))}",
                    "petition_id": petition_id,
                    "event_type": event.get("event_type", "lemma_sync"),
                    "message": event.get("message", "Lemma pod activity"),
                    "metadata": event.get("metadata") or {},
                    "timestamp": event.get("timestamp") or event.get("created_at"),
                    "source": "lemma_pod",
                }
            )
        local.sort(key=lambda e: e.get("timestamp") or "")
    return local


async def _fallback_classify_and_route(
    db: AsyncIOMotorDatabase,
    *,
    petition_id: str,
    area,
    description: str,
    vision_result: dict | None,
    user_override: str | None,
    initial,
):
    classification = initial
    if vision_result and not user_override:
        vision_type = normalize_issue_type(str(vision_result.get("issue_type", "")))
        if vision_type != "other":
            classification = lookup_authority(area, description, vision_type)
            classification.confidence = max(
                classification.confidence,
                float(vision_result.get("confidence", 0.5)),
            )
            classification.reasoning = (
                f"{vision_result.get('reasoning', '')} Routed to {classification.department}."
            ).strip()
    elif user_override:
        classification = lookup_authority(area, description, user_override)

    authority_source = classification.authority_source

    if (
        settings.authority_discovery_enabled
        and not classification.has_contact
        and authority_source not in {"verified", "cpgrams"}
    ):
        try:
            discovered = await discover_with_timeout(
                area,
                description,
                issue_type=classification.issue_type,
                timeout_seconds=settings.authority_discovery_timeout_seconds,
            )
            if discovered and discovered.department_email:
                classification = discovered
                authority_source = "web_search"
        except Exception as exc:
            logger.warning("Web authority discovery failed: %s", exc)

    if not classification.department_email and authority_source not in {"web_search", "lemma"}:
        registry = lookup_authority(area, description, classification.issue_type)
        if registry.department_email:
            classification = registry
            authority_source = "registry"

    return classification, authority_source


async def create_and_process_petition(
    db: AsyncIOMotorDatabase,
    req: CreatePetitionRequest,
    *,
    reporter: dict | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    petition_id = _oid()
    area = await reverse_geocode(req.location.lat, req.location.lng)
    lemma_powered = False

    if not req.location.address and area.display_name:
        req.location.address = area.display_name

    doc = {
        "_id": petition_id,
        "photo_url": req.photo_url,
        "location": req.location.model_dump(),
        "description": req.description,
        "area_info": {
            "display_name": area.display_name,
            "city": area.city,
            "district": area.district,
            "suburb": area.suburb,
            "municipality": area.municipality,
            "state": area.state,
            "country": area.country,
            "postcode": area.postcode,
        },
        "status": PetitionStatus.DRAFT.value,
        "lemma_powered": False,
        "created_at": now,
        "updated_at": now,
    }
    if reporter:
        doc["reporter_user_id"] = reporter["_id"]
        doc["reporter_email"] = reporter.get("email", "")
        doc["reporter_name"] = reporter.get("name", "")
    await db.petitions.insert_one(doc)
    await log_activity(db, petition_id, "created", f"Petition created — area: {area.display_name}")

    vision_result: dict | None = req.vision_classification
    if not vision_result and settings.vision_enabled:
        try:
            vision_result = await classify_image(req.photo_url, description=req.description)
            await log_activity(
                db,
                petition_id,
                "vision_classified",
                f"Vision: {vision_result.get('issue_type')} ({int(float(vision_result.get('confidence', 0)) * 100)}%)",
                vision_result,
            )
        except Exception as exc:
            logger.warning("Vision classification failed: %s", exc)

    user_override = req.vision_issue_type_override
    if user_override:
        user_override = normalize_issue_type(user_override)

    processing_path = "fallback"
    lemma_invocations: list[str] = []
    lemma_pod_petition_id: str | None = None
    lemma_workflow_run_id: str | None = None
    classification = lookup_authority(area, req.description)
    authority_source = classification.authority_source
    draft: EmailDraft | None = None
    lemma_powered = False

    if lemma_service.is_lemma_available():
        try:
            lemma_result = await run_lemma_intake(
                petition_id=petition_id,
                photo_url=req.photo_url,
                description=req.description,
                location=req.location.model_dump(),
                area=area,
            )
            lemma_invocations = lemma_result.invocations
            lemma_pod_petition_id = lemma_result.pod_petition_id
            lemma_workflow_run_id = lemma_result.workflow_run_id
            if lemma_result.success and lemma_result.classification and lemma_result.draft:
                classification = lemma_result.classification
                draft = lemma_result.draft
                authority_source = lemma_result.authority_source
                processing_path = "lemma"
                lemma_powered = True
                await log_activity(
                    db,
                    petition_id,
                    "classified",
                    f"[Lemma] {classification.reasoning}",
                    {**classification.model_dump(), "authority_source": authority_source, "lemma": True},
                )
            else:
                logger.warning(
                    "[fallback] Lemma intake incomplete for %s: %s",
                    petition_id,
                    lemma_result.error,
                )
                lemma_service.mark_fallback_path_active()
        except Exception as exc:
            logger.warning("[fallback] Lemma intake failed for %s: %s", petition_id, exc)
            lemma_service.mark_fallback_path_active()
    else:
        lemma_service.mark_fallback_path_active()

    if processing_path == "fallback":
        classification, authority_source = await _fallback_classify_and_route(
            db,
            petition_id=petition_id,
            area=area,
            description=req.description,
            vision_result=vision_result,
            user_override=user_override,
            initial=classification,
        )
        draft = draft_complaint_email(
            classification.issue_type,
            classification.department,
            classification.department_email or "pending@verify.local",
            req.location,
            req.description,
            req.photo_url,
            area_display=area.display_name,
            city=area.city,
        )
        await log_activity(
            db,
            petition_id,
            "classified",
            f"[Fallback] {classification.reasoning}",
            {**classification.model_dump(), "authority_source": authority_source},
        )

    if user_override and processing_path == "fallback":
        classification = lookup_authority(area, req.description, user_override)
        classification.reasoning = (
            f"Citizen overrode vision prediction to '{user_override.replace('_', ' ')}'. "
            f"{classification.reasoning}"
        )
        if vision_result:
            vision_result = {**vision_result, "user_override": user_override}

    assert draft is not None

    severity_result: dict | None = None
    try:
        severity_result = await analyze_severity(
            db,
            issue_type=classification.issue_type,
            lat=req.location.lat,
            lng=req.location.lng,
            description=req.description,
            vision_confidence=float(vision_result.get("confidence", 0.5)) if vision_result else 0.5,
        )
    except Exception as exc:
        logger.warning("Severity analysis failed: %s", exc)

    ai_explanations = build_ai_explanations(
        vision=vision_result,
        classification=classification.model_dump(),
        severity=severity_result,
        authority_source=authority_source,
        user_override=user_override,
    )

    update_fields: dict[str, Any] = {
        "issue_type": classification.issue_type,
        "department": classification.department,
        "department_email": classification.department_email,
        "contact_channel": classification.contact_channel,
        "contact_value": classification.contact_value,
        "source_url": classification.source_url,
        "authority_source": authority_source,
        "classification_confidence": classification.confidence,
        "complaint_email_subject": draft.subject,
        "complaint_email_draft": draft.body,
        "lemma_powered": lemma_powered,
        "processing_path": processing_path,
        "lemma_invocations": lemma_invocations,
        "lemma_pod_petition_id": lemma_pod_petition_id,
        "lemma_workflow_run_id": lemma_workflow_run_id,
        "updated_at": datetime.now(timezone.utc),
    }
    if vision_result:
        update_fields["vision_classification"] = vision_result
    if severity_result:
        update_fields["severity_score"] = severity_result["severity_score"]
        update_fields["severity_level"] = severity_result["severity_level"]
        update_fields["severity_factors"] = severity_result.get("factors", {})
        if severity_result.get("severity_explanation"):
            update_fields["severity_explanation"] = severity_result["severity_explanation"]
        if severity_result.get("infrastructure") is not None:
            update_fields["infrastructure"] = severity_result["infrastructure"]
    if ai_explanations:
        update_fields["ai_explanations"] = ai_explanations

    await db.petitions.update_one(
        {"_id": petition_id},
        {"$set": update_fields},
    )
    await log_activity(
        db,
        petition_id,
        "drafted",
        f"Complaint drafted for {classification.department} ({classification.contact_channel})",
    )
    await log_activity(db, petition_id, "approval_pending", "Awaiting citizen approval")

    return (await get_petition(db, petition_id)) or {}


async def approve_and_send(
    db: AsyncIOMotorDatabase,
    petition_id: str,
    req: ApprovalRequest,
    *,
    sender: dict | None = None,
) -> dict:
    petition = await get_petition(db, petition_id)
    if not petition:
        raise ValueError("Petition not found")

    if not req.approved:
        await log_activity(db, petition_id, "status_changed", "Email rejected by citizen")
        return petition

    channel = str(petition.get("contact_channel") or "email").lower()
    contact_value = str(petition.get("contact_value") or "").strip()

    if channel in {"portal", "helpline", "cpgrams"} and not (req.to_email or "").strip():
        now = datetime.now(timezone.utc)
        updates = {
            "complaint_email_subject": req.subject,
            "complaint_email_draft": req.body,
            "status": PetitionStatus.SUBMITTED.value,
            "submitted_at": now,
            "updated_at": now,
        }
        if req.is_escalation:
            updates = {
                "escalation_email_draft": req.body,
                "status": PetitionStatus.ESCALATED.value,
                "escalated_at": now,
                "updated_at": now,
            }
        channel_label = {"portal": "official portal", "helpline": "helpline", "cpgrams": "CPGRAMS"}.get(
            channel, channel
        )
        msg = (
            f"Complaint approved for filing via {channel_label}: {contact_value}. "
            "Copy the draft text and submit on the official channel."
        )
        await db.petitions.update_one({"_id": petition_id}, {"$set": updates})
        await log_activity(
            db,
            petition_id,
            "contact_filed",
            msg,
            {"channel": channel, "value": contact_value, "source_url": petition.get("source_url")},
        )
        result_petition = (await get_petition(db, petition_id)) or {}
        result_petition["email_sent"] = False
        result_petition["contact_filed"] = True
        result_petition["send_message"] = msg
        return result_petition

    to_email = (req.to_email or "").strip() or petition.get("department_email") or settings.demo_email_to
    if not to_email:
        raise ValueError("Recipient email is required — enter the municipal authority email before sending")
    intended_to = to_email
    if settings.use_demo_email_redirect:
        to_email = settings.demo_email_to

    sent = False
    send_message = ""
    send_from = settings.smtp_from
    sent_via = ""

    if petition.get("lemma_powered") and lemma_service.is_lemma_available():
        pod_target = str(petition.get("lemma_pod_petition_id") or petition_id)
        try:
            result = await asyncio.wait_for(
                lemma_service.send_email_with_lemma(
                    petition_id=pod_target,
                    subject=req.subject,
                    body=req.body,
                    to_email=to_email,
                    approved=True,
                    is_escalation=req.is_escalation,
                ),
                timeout=settings.lemma_pipeline_timeout_seconds,
            )
            send_message = result.get("message", "")
            sent_via = "lemma_function"
        except Exception as exc:
            logger.warning("Lemma send_complaint_email failed: %s", exc)

    if settings.google_auth_enabled and sender:
        refresh_token = (sender.get("google_refresh_token") or "").strip()
        if not refresh_token:
            raise ValueError(
                "Gmail is not connected. Open Profile → Connect Gmail, sign in again, "
                "then approve and send so the email appears in your Sent folder."
            )
        if not sender.get("email"):
            raise ValueError("Your Google account email is missing — sign in again from Profile.")

        try:
            sent, gmail_error = await send_gmail_as_user(
                refresh_token=refresh_token,
                from_email=sender["email"],
                to_email=to_email,
                subject=req.subject,
                body=req.body,
            )
        except Exception as exc:
            logger.warning("Gmail send failed: %s", exc)
            raise ValueError(
                "Gmail send failed. Open Profile → Connect Gmail to re-authorize, then try again."
            ) from exc

        if not sent:
            raise ValueError(gmail_error or "Gmail send failed. Try again from Profile → Connect Gmail.")

        send_from = sender["email"]
        sent_via = "gmail"
        send_message = f"Email sent from {sender['email']} via Gmail"
        if settings.use_demo_email_redirect and intended_to != to_email:
            send_message += f" (demo delivery to {to_email}; authority: {intended_to})"

    elif sender and sender.get("google_refresh_token") and sender.get("email"):
        try:
            sent, _gmail_error = await send_gmail_as_user(
                refresh_token=sender["google_refresh_token"],
                from_email=sender["email"],
                to_email=to_email,
                subject=req.subject,
                body=req.body,
            )
            if sent:
                send_from = sender["email"]
                sent_via = "gmail"
                send_message = f"Email sent from {sender['email']} via Gmail"
                if settings.use_demo_email_redirect and intended_to != to_email:
                    send_message += f" (demo delivery to {to_email}; authority: {intended_to})"
        except Exception as exc:
            logger.warning("Gmail send failed, trying fallbacks: %s", exc)

    if not sent:
        sent = send_email(to_email, req.subject, req.body)
        if sent:
            sent_via = "smtp"
            send_message = f"Email sent via SMTP from {settings.smtp_from}"
            if settings.use_demo_email_redirect and intended_to != to_email:
                send_message += f" (demo delivery; authority: {intended_to})"
        else:
            send_message = "Email logged (configure SMTP in .env)"
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
        if send_message:
            msg = f"{msg} — {send_message}"
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
        if send_message:
            msg = f"{msg} — {send_message}"

    await db.petitions.update_one({"_id": petition_id}, {"$set": updates})
    await log_activity(
        db,
        petition_id,
        event,
        msg,
        {
            "to": to_email,
            "intended_to": intended_to,
            "smtp_sent": sent,
            "from": send_from,
            "sent_via": sent_via or ("gmail" if sent and sender else "smtp" if sent else ""),
            "demo_redirect": settings.use_demo_email_redirect,
        },
    )

    result_petition = (await get_petition(db, petition_id)) or {}
    result_petition["email_sent"] = sent
    result_petition["sent_to"] = to_email
    result_petition["intended_to"] = intended_to
    result_petition["send_message"] = send_message
    return result_petition


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

    original_url = petition.get("photo_url", "")
    verdict_data: dict[str, Any]
    try:
        verdict_data = await verify_resolution(
            original_url=original_url,
            follow_up_url=follow_up_photo_url,
            issue_type=petition.get("issue_type") or "other",
            description=petition.get("description", ""),
        )
    except Exception as exc:
        logger.warning("Resolution verification failed, using heuristic: %s", exc)
        local = check_resolution(
            petition.get("issue_type") or "other",
            petition.get("description", ""),
        )
        verdict_data = local.model_dump()

    if petition.get("lemma_powered") and lemma_service.is_lemma_available():
        pod_target = str(petition.get("lemma_pod_petition_id") or petition_id)
        try:
            await asyncio.wait_for(
                lemma_service.update_resolution_in_pod(petition_id=pod_target, verdict=verdict_data),
                timeout=settings.lemma_pipeline_timeout_seconds,
            )
        except Exception as exc:
            logger.warning("Lemma update_resolution_status failed: %s", exc)

    status = verdict_data.get("recommended_status") or (
        "resolved" if verdict_data.get("resolved") else "under_review"
    )
    updates: dict = {
        "resolution_verdict": verdict_data,
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
        verdict_data.get("reasoning", "Resolution checked"),
        verdict_data,
    )

    return (await get_petition(db, petition_id)) or {}


async def find_stale_for_escalation(
    db: AsyncIOMotorDatabase,
    reporter_user_id: str | None = None,
) -> dict | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.escalation_days)
    query: dict = {
        "status": PetitionStatus.SUBMITTED.value,
        "submitted_at": {"$lte": cutoff},
        "escalation_email_draft": {"$exists": False},
    }
    if reporter_user_id:
        query["reporter_user_id"] = reporter_user_id
    cursor = db.petitions.find(query).sort("submitted_at", 1).limit(1)

    async for doc in cursor:
        return _serialize(doc)
    return None


async def prepare_escalation(
    db: AsyncIOMotorDatabase,
    petition_id: str | None = None,
    reporter_user_id: str | None = None,
) -> dict | None:
    petition = (
        await get_petition(db, petition_id)
        if petition_id
        else await find_stale_for_escalation(db, reporter_user_id)
    )
    if not petition:
        return None

    pid = petition["id"]
    draft = draft_escalation_email(petition)
    escalation_invocations: list[str] = []

    if lemma_service.is_lemma_available():
        try:
            wf = await asyncio.wait_for(
                lemma_service.run_escalation_pipeline(),
                timeout=settings.lemma_pipeline_timeout_seconds,
            )
            if wf.get("run_id"):
                escalation_invocations.append("workflow:escalation-pipeline")
            pod_result = await asyncio.wait_for(
                lemma_service.escalate_petition_in_pod(
                    petition_id=str(petition.get("lemma_pod_petition_id") or pid),
                ),
                timeout=settings.lemma_pipeline_timeout_seconds,
            )
            escalation_invocations.append("function:escalate_petition")
            if pod_result.get("subject") and pod_result.get("body"):
                draft = EmailDraft(
                    subject=str(pod_result["subject"]),
                    body=str(pod_result["body"]),
                    to_email=str(pod_result.get("to_email") or draft.to_email),
                )
        except Exception as exc:
            logger.warning("Lemma escalation pipeline failed, using local draft: %s", exc)

    await db.petitions.update_one(
        {"_id": pid},
        {
            "$set": {
                "escalation_email_draft": draft.body,
                "status": PetitionStatus.UNDER_REVIEW.value,
                "updated_at": datetime.now(timezone.utc),
                "lemma_invocations": list(dict.fromkeys(
                    (petition.get("lemma_invocations") or []) + escalation_invocations
                )),
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
