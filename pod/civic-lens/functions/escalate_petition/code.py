#input_type_name: EscalatePetitionInput
#output_type_name: EscalatePetitionOutput
#function_name: escalate_petition

import os
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod


class EscalatePetitionInput(BaseModel):
    petition_id: str | None = None
    days_threshold: int | None = None


class EscalatePetitionOutput(BaseModel):
    petition_id: str | None
    escalation_drafted: bool
    subject: str | None = None
    body: str | None = None
    to_email: str | None = None
    message: str


def _draft_escalation(petition: dict) -> tuple[str, str]:
    loc = petition.get("location") or {}
    address = loc.get("address", "the reported location")
    issue = petition.get("issue_type", "civic issue")
    dept = petition.get("department", "Municipal Department")
    submitted = petition.get("submitted_at", "recently")

    subject = f"ESCALATION: Unresolved {issue.replace('_', ' ').title()} — {address}"
    body = f"""Dear {dept} Team,

This is a follow-up escalation regarding a citizen complaint submitted on {submitted}.

Issue type: {issue.replace('_', ' ').title()}
Location: {address}
Coordinates: {loc.get('lat')}, {loc.get('lng')}

The original complaint was submitted more than {os.getenv('ESCALATION_DAYS', '3')} days ago and remains unresolved. The citizen has not received confirmation of repair or resolution.

We respectfully request:
1. An update on the status of this complaint
2. Expected timeline for resolution
3. A reference/ticket number if one was not previously provided

Original description:
{petition.get('description', 'N/A')}

Thank you for your prompt attention.

A concerned citizen of Metro City
"""
    return subject, body


async def escalate_petition(ctx: FunctionContext, data: EscalatePetitionInput) -> EscalatePetitionOutput:
    pod = Pod.from_env()
    days = data.days_threshold or int(os.getenv("ESCALATION_DAYS", "3"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    petition_id = data.petition_id
    if not petition_id:
        rows = pod.records.list(
            "petitions",
            limit=50,
            filter=[{"field": "status", "op": "eq", "value": "submitted"}],
            sort=[{"field": "submitted_at", "direction": "asc"}],
        ).to_dict()["items"]

        stale = None
        for row in rows:
            submitted_at = row.get("submitted_at")
            if not submitted_at:
                continue
            try:
                submitted_dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if submitted_dt <= cutoff and not row.get("escalation_email_draft"):
                stale = row
                break

        if not stale:
            return EscalatePetitionOutput(
                petition_id=None,
                escalation_drafted=False,
                message="No stale petitions found",
            )
        petition_id = stale["id"]
        petition = stale
    else:
        petition = pod.table("petitions").get(petition_id)

    subject, body = _draft_escalation(petition)
    to_email = petition.get("department_email") or os.getenv("DEMO_EMAIL_TO", "municipal-demo@example.com")

    pod.table("petitions").update(
        petition_id,
        {
            "escalation_email_draft": body,
            "status": "under_review",
        },
    )

    pod.table("activity_log").create(
        {
            "petition_id": petition_id,
            "event_type": "escalation_pending",
            "message": "Escalation email drafted — awaiting citizen approval",
            "metadata": {"subject": subject, "to": to_email},
        }
    )

    return EscalatePetitionOutput(
        petition_id=petition_id,
        escalation_drafted=True,
        subject=subject,
        body=body,
        to_email=to_email,
        message="Escalation draft ready for approval",
    )
