import logging
import re
from datetime import datetime, timezone

from app.models import ClassificationResult, EmailDraft, Location, ResolutionVerdict
from app.services.departments import DEPARTMENT_BY_ISSUE, DEPARTMENTS, ISSUE_KEYWORDS

logger = logging.getLogger(__name__)


def classify_issue(description: str, location: Location) -> ClassificationResult:
    text = description.lower()
    scores: dict[str, int] = {k: 0 for k in ISSUE_KEYWORDS}

    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[issue_type] += 2 if " " in kw else 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "other"

    dept_name = DEPARTMENT_BY_ISSUE.get(best, DEPARTMENT_BY_ISSUE["other"])
    dept = next(d for d in DEPARTMENTS if d["name"] == dept_name)
    confidence = min(0.95, 0.5 + scores[best] * 0.15)

    return ClassificationResult(
        issue_type=best,
        department=dept["name"],
        department_email=dept["contact_email"],
        confidence=confidence,
        reasoning=f"Matched keywords for '{best}' in citizen description. Routed to {dept['name']}.",
    )


def draft_complaint_email(
    issue_type: str,
    department: str,
    department_email: str,
    location: Location,
    description: str,
    photo_url: str,
) -> EmailDraft:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    issue_label = issue_type.replace("_", " ").title()
    address = location.address or f"coordinates {location.lat:.5f}, {location.lng:.5f}"

    subject = f"Citizen Complaint: {issue_label} at {address}"
    body = f"""Dear {department} Team,

I am writing to formally report a civic issue within Metro City Municipal Corporation jurisdiction.

Issue Type: {issue_label}
Location: {address}
Coordinates: {location.lat}, {location.lng}
Date Observed: {today}

Description:
{description or 'Please see attached photographic evidence.'}

I have documented this issue with a photograph ({photo_url}) and respectfully request that your department:
1. Inspect the reported location at the earliest convenience
2. Take remedial action to resolve this issue
3. Provide an acknowledgment with a reference/ticket number

This matter affects public safety and quality of life in our community. I would appreciate an update within 5 business days.

Thank you for your attention to this matter.

A concerned citizen of Metro City
"""

    return EmailDraft(subject=subject, body=body, to_email=department_email)


def draft_escalation_email(petition: dict) -> EmailDraft:
    loc = petition.get("location") or {}
    address = loc.get("address") or f"{loc.get('lat')}, {loc.get('lng')}"
    issue = (petition.get("issue_type") or "civic issue").replace("_", " ").title()
    dept = petition.get("department", "Municipal Department")
    submitted = petition.get("submitted_at", "recently")
    if isinstance(submitted, datetime):
        submitted = submitted.strftime("%B %d, %Y")

    subject = f"ESCALATION: Unresolved {issue} — {address}"
    body = f"""Dear {dept} Team,

This is a follow-up escalation regarding a citizen complaint submitted on {submitted}.

Issue type: {issue}
Location: {address}
Coordinates: {loc.get('lat')}, {loc.get('lng')}

The original complaint remains unresolved after the expected response period. The citizen has not received confirmation of repair or resolution.

Original description:
{petition.get('description', 'N/A')}

We respectfully request an update on status, expected timeline, and a reference number.

A concerned citizen of Metro City
"""
    return EmailDraft(
        subject=subject,
        body=body,
        to_email=petition.get("department_email", "municipal-demo@example.com"),
    )


def check_resolution(
    issue_type: str,
    description: str,
    follow_up_description: str = "",
) -> ResolutionVerdict:
    """Heuristic resolution check for demo when vision model unavailable."""
    text = (follow_up_description or description).lower()
    resolved_signals = [
        "fixed", "repaired", "clean", "resolved", "filled", "working", "cleared", "patched"
    ]
    unresolved_signals = ["still", "broken", "unchanged", "worse", "overflowing", "dark"]

    resolved_score = sum(1 for s in resolved_signals if s in text)
    unresolved_score = sum(1 for s in unresolved_signals if s in text)

    if follow_up_description and resolved_score > unresolved_score:
        return ResolutionVerdict(
            resolved=True,
            confidence=0.75,
            reasoning=f"Follow-up description suggests the {issue_type.replace('_', ' ')} issue may be resolved.",
            recommended_status="resolved",
        )

    return ResolutionVerdict(
        resolved=False,
        confidence=0.6,
        reasoning=f"Insufficient evidence that the {issue_type.replace('_', ' ')} issue is resolved. Manual review recommended.",
        recommended_status="under_review",
    )
