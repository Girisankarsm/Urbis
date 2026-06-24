#input_type_name: SendComplaintEmailInput
#output_type_name: SendComplaintEmailOutput
#function_name: send_complaint_email

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import BaseModel
from lemma_sdk import FunctionContext, Pod

logger = logging.getLogger(__name__)


class SendComplaintEmailInput(BaseModel):
    petition_id: str
    subject: str
    body: str
    to_email: str | None = None
    approved: bool = True
    is_escalation: bool = False


class SendComplaintEmailOutput(BaseModel):
    petition_id: str
    status: str
    email_sent: bool
    message: str


def _send_smtp(to_email: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        logger.info("SMTP not configured — logging email only")
        logger.info("TO: %s | SUBJECT: %s\n%s", to_email, subject, body)
        return False

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "civiclens@demo.local")

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.sendmail(from_addr, [to_email], msg.as_string())
    return True


async def send_complaint_email(ctx: FunctionContext, data: SendComplaintEmailInput) -> SendComplaintEmailOutput:
    pod = Pod.from_env()

    if not data.approved:
        pod.table("activity_log").create(
            {
                "petition_id": data.petition_id,
                "event_type": "status_changed",
                "message": "Complaint email rejected by citizen",
            }
        )
        return SendComplaintEmailOutput(
            petition_id=data.petition_id,
            status="draft",
            email_sent=False,
            message="Rejected by user",
        )

    petition = pod.table("petitions").get(data.petition_id)
    to_email = data.to_email or petition.get("department_email") or os.getenv("DEMO_EMAIL_TO", "municipal-demo@example.com")

    sent = _send_smtp(to_email, data.subject, data.body)
    now = datetime.now(timezone.utc).isoformat()

    if data.is_escalation:
        updates = {
            "escalation_email_draft": data.body,
            "status": "escalated",
            "escalated_at": now,
        }
        event_type = "escalation_sent"
        event_msg = f"Escalation email {'sent' if sent else 'logged (demo mode)'} to {to_email}"
        final_status = "escalated"
    else:
        updates = {
            "complaint_email_subject": data.subject,
            "complaint_email_draft": data.body,
            "status": "submitted",
            "submitted_at": now,
        }
        event_type = "email_sent"
        event_msg = f"Complaint email {'sent' if sent else 'logged (demo mode)'} to {to_email}"
        final_status = "submitted"

    pod.table("petitions").update(data.petition_id, updates)

    pod.table("activity_log").create(
        {
            "petition_id": data.petition_id,
            "event_type": event_type,
            "message": event_msg,
            "metadata": {"to": to_email, "subject": data.subject, "smtp_sent": sent},
        }
    )

    return SendComplaintEmailOutput(
        petition_id=data.petition_id,
        status=final_status,
        email_sent=sent,
        message="Email sent" if sent else "Email logged (SMTP not configured)",
    )
