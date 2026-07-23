from pydantic import BaseModel, ConfigDict, Field

from app.schemas.issue import IssueStatus


class AccountStatusUpdate(BaseModel):
    is_active: bool = Field(alias="isActive")


class OperatorSuspensionUpdate(BaseModel):
    suspended: bool


class ExpertVerificationUpdate(BaseModel):
    is_verified: bool = Field(alias="isVerified")


class IssueExpertOverride(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    expert_id: int = Field(alias="expertId")


class IssuePriorityOverride(BaseModel):
    priority: str | None = None
    urgency: str | None = None


class IssueOverride(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assigned_expert_id: int | None = Field(default=None, alias="assignedExpertId")
    priority: str | None = None
    urgency: str | None = None
    status: IssueStatus | None = None


class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_users: int = Field(alias="totalUsers")
    total_experts: int = Field(alias="totalExperts")
    total_verified_experts: int = Field(alias="totalVerifiedExperts")
    total_issues: int = Field(alias="totalIssues")
    issues_by_status: dict[str, int] = Field(alias="issuesByStatus")
