from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin, get_db
from app.models.user import User
from app.schemas.admin import (
    AccountStatusUpdate,
    AnalyticsResponse,
    ExpertVerificationUpdate,
    IssueExpertOverride,
    IssueOverride,
    IssuePriorityOverride,
)
from app.schemas.expert import ExpertResponse
from app.schemas.issue import IssueResponse, IssueSummaryResponse
from app.schemas.user import UserResponse
from app.services.admin_service import (
    get_analytics,
    list_experts,
    list_expert_applications,
    list_issues,
    list_users,
    override_issue_expert,
    override_issue,
    override_issue_priority,
    set_expert_active,
    set_expert_verified,
    set_user_active,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/users", response_model=list[UserResponse])
def admin_list_users(db: Session = Depends(get_db)):
    return list_users(db)


@router.get("/experts", response_model=list[ExpertResponse])
def admin_list_experts(db: Session = Depends(get_db)):
    return list_experts(db)


@router.get("/experts/applications", response_model=list[ExpertResponse])
def admin_list_expert_applications(db: Session = Depends(get_db)):
    return list_expert_applications(db)


@router.get("/issues", response_model=list[IssueSummaryResponse])
def admin_list_issues(db: Session = Depends(get_db)):
    return list_issues(db)


@router.patch("/issues/{issue_id}/override", response_model=IssueResponse)
def admin_override_issue(
    issue_id: int,
    data: IssueOverride,
    db: Session = Depends(get_db),
):
    if all(
        value is None
        for value in (
            data.assigned_expert_id,
            data.priority,
            data.urgency,
            data.status,
        )
    ):
        raise HTTPException(status_code=400, detail="Provide at least one override field")

    issue = override_issue(
        db,
        issue_id,
        assigned_expert_id=data.assigned_expert_id,
        priority=data.priority,
        urgency=data.urgency,
        status=data.status.value if data.status is not None else None,
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue or expert not found")
    return issue


@router.patch("/issues/{issue_id}/override-expert", response_model=IssueResponse)
def admin_override_issue_expert(
    issue_id: int,
    data: IssueExpertOverride,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    issue = override_issue_expert(db, issue_id, data.expert_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue or expert not found")
    return issue


@router.patch("/issues/{issue_id}/override-priority", response_model=IssueResponse)
def admin_override_issue_priority(
    issue_id: int,
    data: IssuePriorityOverride,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if data.priority is None and data.urgency is None:
        raise HTTPException(status_code=400, detail="Priority or urgency is required")

    issue = override_issue_priority(db, issue_id, data.priority, data.urgency)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.patch("/experts/{expert_id}/verify", response_model=ExpertResponse)
def verify_expert(
    expert_id: int,
    data: ExpertVerificationUpdate,
    db: Session = Depends(get_db),
):
    expert = set_expert_verified(db, expert_id, data.is_verified)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    data: AccountStatusUpdate,
    db: Session = Depends(get_db),
):
    user = set_user_active(db, user_id, data.is_active)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/experts/{expert_id}/status", response_model=ExpertResponse)
def update_expert_status(
    expert_id: int,
    data: AccountStatusUpdate,
    db: Session = Depends(get_db),
):
    expert = set_expert_active(db, expert_id, data.is_active)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(db: Session = Depends(get_db)):
    return get_analytics(db)


@router.get("/overview", response_model=AnalyticsResponse)
def overview(db: Session = Depends(get_db)):
    return get_analytics(db)
