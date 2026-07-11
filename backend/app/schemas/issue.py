from datetime import date, datetime

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class IssueStatus(StrEnum):
    open = "open"
    ai_classified = "ai_classified"
    waiting_for_assignment = "waiting_for_assignment"
    assigned = "assigned"
    accepted = "accepted"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IssueUrgency(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueAttachmentResponse(CamelModel):
    id: int
    file_url: str = Field(alias="fileUrl")
    file_type: str = Field(alias="fileType")
    file_size: int | None = Field(default=None, alias="fileSize")
    original_filename: str | None = Field(default=None, alias="originalFilename")
    content_type: str | None = Field(default=None, alias="contentType")
    size_bytes: int | None = Field(default=None, alias="sizeBytes")
    storage_provider: str = Field(alias="storageProvider")
    created_at: datetime = Field(alias="createdAt")


class IssueCreate(CamelModel):
    title: str
    description: str
    problem_type: str | None = Field(default=None, alias="problemType")
    category: str | None = None
    priority: str | None = None
    urgency: str | None = None
    required_skills: list[str] | None = Field(default=None, alias="requiredSkills")
    preferred_visit_date: date | None = Field(default=None, alias="preferredVisitDate")
    preferred_time: str | None = Field(default=None, alias="preferredTime")
    location: str | None = None
    pin_code: str | None = Field(default=None, alias="pinCode")
    address: str | None = None
    image_path: str | None = Field(default=None, alias="imagePath")
    video_path: str | None = Field(default=None, alias="videoPath")
    audio_path: str | None = Field(default=None, alias="audioPath")

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
    problem_type: str | None = Field(default=None, alias="problemType")
    priority: str | None = None
    urgency: str | None = None
    required_skills: list[str] | None = Field(default=None, alias="requiredSkills")

    status: IssueStatus | None = None
    preferred_visit_date: date | None = Field(default=None, alias="preferredVisitDate")
    preferred_time: str | None = Field(default=None, alias="preferredTime")
    location: str | None = None
    pin_code: str | None = Field(default=None, alias="pinCode")
    address: str | None = None
    image_path: str | None = Field(default=None, alias="imagePath")
    video_path: str | None = Field(default=None, alias="videoPath")
    audio_path: str | None = Field(default=None, alias="audioPath")

    @field_validator("required_skills", mode="before")
    @classmethod
    def normalize_required_skills(cls, value):
        if value is None or isinstance(value, list):
            return value
        return [skill.strip() for skill in str(value).split(",") if skill.strip()]


class IssueResponse(CamelModel):
    id: int
    title: str
    description: str

    category: str | None = None
    problem_type: str | None = Field(default=None, alias="problemType")
    priority: str | None = None
    urgency: str | None = None
    required_skills: list[str] | None = Field(default=None, alias="requiredSkills")
    confidence_score: float | None = Field(default=None, alias="confidenceScore")
    ai_explanation: str | None = Field(default=None, alias="aiExplanation")

    status: str

    preferred_visit_date: date | None = Field(default=None, alias="preferredVisitDate")
    preferred_time: str | None = Field(default=None, alias="preferredTime")
    location: str | None = None
    pin_code: str | None = Field(default=None, alias="pinCode")
    address: str | None = None
    image_path: str | None = Field(default=None, alias="imagePath")
    video_path: str | None = Field(default=None, alias="videoPath")
    audio_path: str | None = Field(default=None, alias="audioPath")
    attachments: list[IssueAttachmentResponse] = Field(default_factory=list)

    customer_id: int
    assigned_expert_id: int | None = None
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
    urgency: str | None = None
    status: str
    location: str | None = None
    pin_code: str | None = Field(default=None, alias="pinCode")
    assigned_expert_id: int | None = None
    created_at: datetime


class IssueClassificationResponse(CamelModel):
    id: int
    problem_type: str = Field(alias="problemType")
    category: str
    priority: str
    urgency: str | None = None
    required_skills: list[str] = Field(alias="requiredSkills")
    confidence_score: float | None = Field(default=None, alias="confidenceScore")
    ai_explanation: str | None = Field(default=None, alias="aiExplanation")

    @field_validator("required_skills", mode="before")
    @classmethod
    def split_required_skills(cls, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [skill.strip() for skill in str(value).split(",") if skill.strip()]


class IssueStatusUpdate(BaseModel):
    status: IssueStatus
