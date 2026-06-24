from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PetitionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class Location(BaseModel):
    address: str = ""
    lat: float
    lng: float


class Department(BaseModel):
    id: str | None = None
    name: str
    issue_types: list[str]
    contact_email: str
    jurisdiction_area: str


class ActivityEvent(BaseModel):
    id: str | None = None
    petition_id: str
    event_type: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None


class Petition(BaseModel):
    id: str | None = None
    issue_type: str | None = None
    photo_url: str
    follow_up_photo_url: str | None = None
    location: Location
    description: str = ""
    department: str | None = None
    department_email: str | None = None
    status: PetitionStatus = PetitionStatus.DRAFT
    complaint_email_draft: str | None = None
    complaint_email_subject: str | None = None
    escalation_email_draft: str | None = None
    resolution_verdict: dict[str, Any] | None = None
    workflow_run_id: str | None = None
    submitted_at: datetime | None = None
    resolved_at: datetime | None = None
    escalated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreatePetitionRequest(BaseModel):
    photo_url: str
    location: Location
    description: str = ""


class ApprovalRequest(BaseModel):
    subject: str
    body: str
    approved: bool = True
    is_escalation: bool = False


class FollowUpRequest(BaseModel):
    follow_up_photo_url: str


class ClassificationResult(BaseModel):
    issue_type: str
    department: str
    department_email: str
    confidence: float
    reasoning: str


class EmailDraft(BaseModel):
    subject: str
    body: str
    to_email: str


class ResolutionVerdict(BaseModel):
    resolved: bool
    confidence: float
    reasoning: str
    recommended_status: str
