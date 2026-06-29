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


class VisionClassification(BaseModel):
    issue_type: str
    confidence: float
    reasoning: str
    source: str = "keyword"
    user_override: str | None = None


class SeverityAnalysis(BaseModel):
    severity_score: int
    severity_level: str
    reasoning: str
    factors: dict[str, Any] = Field(default_factory=dict)


class AIExplanations(BaseModel):
    vision_classification: dict[str, Any] | None = None
    authority_routing: dict[str, Any] | None = None
    severity_analysis: dict[str, Any] | None = None


class DuplicateMatch(BaseModel):
    petition_id: str
    issue_type: str
    status: str | None = None
    distance_m: float
    image_similarity: float | None = None
    likelihood: float
    photo_url: str | None = None
    created_at: str | None = None
    description: str | None = None


class CreatePetitionRequest(BaseModel):
    photo_url: str
    location: Location
    description: str = ""
    vision_issue_type_override: str | None = None
    vision_classification: dict[str, Any] | None = None


class ApprovalRequest(BaseModel):
    subject: str
    body: str
    approved: bool = True
    is_escalation: bool = False
    to_email: str | None = None


class FollowUpRequest(BaseModel):
    follow_up_photo_url: str


class ClassificationResult(BaseModel):
    issue_type: str
    department: str
    department_email: str = ""
    contact_channel: str = "email"
    contact_value: str = ""
    source_url: str = ""
    confidence: float
    reasoning: str
    authority_source: str = "registry"

    @property
    def is_email_channel(self) -> bool:
        return self.contact_channel == "email" and bool(self.department_email or self.contact_value)

    @property
    def effective_contact_value(self) -> str:
        if self.contact_channel == "email":
            return self.department_email or self.contact_value
        return self.contact_value

    @property
    def has_contact(self) -> bool:
        return bool(self.effective_contact_value)


class EmailDraft(BaseModel):
    subject: str
    body: str
    to_email: str


class ResolutionVerdict(BaseModel):
    resolved: bool
    confidence: float
    reasoning: str
    recommended_status: str
    status: str | None = None
    source: str | None = None


class ClassifyVisionRequest(BaseModel):
    photo_url: str
    description: str = ""


class CheckDuplicatesRequest(BaseModel):
    lat: float
    lng: float
    issue_type: str | None = None
    photo_url: str | None = None
