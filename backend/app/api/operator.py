from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_operator, get_db
from app.models.expert import Expert
from app.models.issue import Issue
from app.models.user import User
from app.schemas.issue import IssueResponse
from app.schemas.operator import (
    OperatorDashboardMetrics,
    OperatorExpertVerification,
    OperatorIssueUpdate,
)
from app.services.websocket_manager import publish_issue_update


router = APIRouter(
    prefix="/operator",
    tags=["Operator"],
    dependencies=[Depends(get_current_operator)],
)


@router.get("/dashboard/metrics", response_model=OperatorDashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db)):
    queue_count = (
        db.query(Issue)
        .filter(Issue.status.in_(["submitted", "ai_classified", "operator_review"]))
        .count()
    )
    open_count = db.query(Issue).filter(Issue.status == "open").count()
    available_experts = (
        db.query(Expert)
        .filter(Expert.is_verified.is_(True), Expert.is_active.is_(True))
        .count()
    )
    return {
        "queue_count": queue_count,
        "open_count": open_count,
        "available_experts": available_experts,
    }


@router.patch("/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    data: OperatorIssueUpdate,
    current_operator: User = Depends(get_current_operator),
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    previous_expert_id = issue.assigned_expert_id
    if data.assigned_expert_id is not None:
        expert = db.query(Expert).filter(Expert.id == data.assigned_expert_id).first()
        if expert is None:
            raise HTTPException(status_code=404, detail="Expert not found")
        issue.assigned_expert_id = expert.id
        issue.assigned_at = datetime.now(timezone.utc)

    for field in ("status", "urgency", "priority", "operator_note"):
        value = getattr(data, field)
        if value is not None:
            setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    publish_issue_update(
        issue,
        "operator_issue_updated",
        previous_expert_id=previous_expert_id if data.assigned_expert_id is not None else None,
    )
    return issue


@router.patch("/experts/{expert_id}/verify", response_model=dict)
def verify_expert(
    expert_id: int,
    data: OperatorExpertVerification,
    current_operator: User = Depends(get_current_operator),
    db: Session = Depends(get_db),
):
    expert = db.query(Expert).filter(Expert.id == expert_id).first()
    if expert is None:
        raise HTTPException(status_code=404, detail="Expert not found")

    expert.is_verified = data.is_verified
    db.commit()
    return {"id": expert.id, "is_verified": expert.is_verified}
