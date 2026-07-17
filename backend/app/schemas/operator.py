from pydantic import BaseModel, ConfigDict, StrictInt


class OperatorModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class OperatorIssueUpdate(OperatorModel):
    status: str | None = None
    urgency: str | None = None
    priority: str | None = None
    assigned_expert_id: StrictInt | None = None
    operator_note: str | None = None


class OperatorExpertVerification(BaseModel):
    is_verified: bool


class OperatorDashboardMetrics(OperatorModel):
    queue_count: int
    open_count: int
    available_experts: int
