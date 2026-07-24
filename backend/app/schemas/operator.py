from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.issue import IssueStatus, IssueUrgency


class OperatorModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda value: value.split("_")[0] + "".join(
            word.capitalize() for word in value.split("_")[1:]
        ),
    )


class OperatorIssueUpdate(OperatorModel):
    status: IssueStatus | None = None
    problem_type: str | None = None
    category: str | None = None
    urgency: IssueUrgency | None = None
    priority: IssueUrgency | None = None
    # Browser <select> values are strings.  Accept both the Admin-style
    # expertId and the operator-style assignedExpertId so an assignment is not
    # rejected with 422 before reaching the service layer.
    assigned_expert_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "assigned_expert_id",
            "assignedExpertId",
            "expert_id",
            "expertId",
        ),
    )
    operator_note: str | None = None

    @field_validator("problem_type", "category")
    @classmethod
    def validate_non_empty_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("value must not be blank")
        return value.strip() if value is not None else value


class OperatorExpertVerification(BaseModel):
    is_verified: bool


class OperatorDashboardMetrics(OperatorModel):
    queue_count: int
    open_count: int
    available_experts: int
