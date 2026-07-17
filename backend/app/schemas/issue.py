from datetime import date, datetime

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_camel_case(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_to_camel_case,
        populate_by_name=True,
        from_attributes=True,
    )


class IssueStatus(StrEnum):
    submitted = "submitted"
    ai_classified = "ai_classified"
    waiting_for_assignment = "waiting_for_assignment"
    operator_review = "operator_review"
    need_more_info = "need_more_info"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    closed = "closed"


class IssueUrgency(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueAttachmentResponse(CamelModel):
    id: int
    file_url: str
    file_type: str
    file_size: int | None = None
    original_filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    storage_provider: str
    created_at: datetime


class IssueCreate(CamelModel):
    title: str
    description: str
    problem_type: str | None = None
    category: str | None = None
    priority: str | None = None
    urgency: str | None = None
    required_skills: list[str] | None = None
    preferred_visit_date: date | None = None
    preferred_time: str | None = None
    location: str | None = None
    pin_code: str | None = None
    address: str | None = None
    image_path: str | None = None
    video_path: str | None = None
    audio_path: str | None = None

    @field_validator("required_skills", mode="before")
    @classmethod
    def normalize_required_skills(cls, value):
        if value is None or isinstance(value, list):
            return value
        return [skill.strip() for skill in str(value).split(",") if skill.strip()]


class IssueUpdate(CamelModel):
    title: str | None = None
    description: str | None = None

    category: str | None = None
    problem_type: str | None = None
    priority: str | None = None
    urgency: str | None = None
    required_skills: list[str] | None = None

    status: IssueStatus | None = None
    preferred_visit_date: date | None = None
    preferred_time: str | None = None
    location: str | None = None
    pin_code: str | None = None
    address: str | None = None
    image_path: str | None = None
    video_path: str | None = None
    audio_path: str | None = None

    @field_validator("required_skills", mode="before")
    @classmethod
    def normalize_required_skills(cls, value):
        if value is None or isinstance(value, list):
            return value
        return [skill.strip() for skill in str(value).split(",") if skill.strip()]


class AssignedExpertSummary(CamelModel):
    id: int
    full_name: str
    email: str
    phone: str
    skills: str | None = None
    profile_image_url: str | None = None


class IssueResponse(CamelModel):
    id: int
    title: str
    description: str

    category: str | None = None
    problem_type: str | None = None
    priority: str | None = None
    urgency: str | None = None
    required_skills: list[str] | None = None
    confidence_score: float | None = None
    ai_explanation: str | None = None
    operator_note: str | None = None

    status: str

    preferred_visit_date: date | None = None
    preferred_time: str | None = None
    location: str | None = None
    pin_code: str | None = None
    address: str | None = None
    image_path: str | None = None
    video_path: str | None = None
    audio_path: str | None = None
    attachments: list[IssueAttachmentResponse] = Field(default_factory=list)

    customer_id: int
    assigned_expert_id: int | None = None
    assigned_expert: AssignedExpertSummary | None = None
    assigned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("required_skills", mode="before")
    @classmethod
    def split_required_skills(cls, value):
        if value is None or isinstance(value, list):
            return value
        return [skill.strip() for skill in str(value).split(",") if skill.strip()]


class IssueSummaryResponse(CamelModel):
    id: int
    title: str
    category: str | None = None
    priority: str | None = None
    urgency: str | None = None
    status: str
    location: str | None = None
    pin_code: str | None = None
    assigned_expert_id: int | None = None
    assigned_expert: AssignedExpertSummary | None = None
    assigned_at: datetime | None = None
    updated_at: datetime
    created_at: datetime


class IssueClassificationResponse(CamelModel):
    id: int
    problem_type: str
    category: str
    priority: str
    urgency: str | None = None
    required_skills: list[str]
    confidence_score: float | None = None
    ai_explanation: str | None = None

    @field_validator("required_skills", mode="before")
    @classmethod
    def split_required_skills(cls, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [skill.strip() for skill in str(value).split(",") if skill.strip()]


class IssueStatusUpdate(CamelModel):
    status: IssueStatus
