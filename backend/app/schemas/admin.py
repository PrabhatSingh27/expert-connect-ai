from pydantic import BaseModel, ConfigDict, Field


class AccountStatusUpdate(BaseModel):
    is_active: bool = Field(alias="isActive")


class ExpertVerificationUpdate(BaseModel):
    is_verified: bool = Field(alias="isVerified")


class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_users: int = Field(alias="totalUsers")
    total_experts: int = Field(alias="totalExperts")
    total_verified_experts: int = Field(alias="totalVerifiedExperts")
    total_issues: int = Field(alias="totalIssues")
    issues_by_status: dict[str, int] = Field(alias="issuesByStatus")
