from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_operator, get_db
from app.models.expert import Expert
from app.models.issue import Issue
from app.models.user import User
from app.schemas.issue import IssueResponse, IssueSummaryResponse
from app.schemas.operator import (
    OperatorDashboardMetrics,
    OperatorExpertVerification,
    OperatorIssueUpdate,
)
from app.services.operator_service import (
    get_operator_issue,
    list_operator_issues,
    override_issue_decisions,
)


router = APIRouter(
    prefix="/operator",
    tags=["Operator"],
    dependencies=[Depends(get_current_operator)],
)


@router.get("/dashboard/metrics", response_model=OperatorDashboardMetrics)
def dashboard_metrics(db: Session = Depends(get_db)):
    queue_count = (
        db.query(Issue)
        .filter(Issue.status.in_(["submitted", "ai_classified", "waiting_for_assignment", "operator_review"]))
        .count()
    )
    open_count = db.query(Issue).filter(Issue.status.in_(["assigned", "in_progress"])).count()
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


@router.get("/issues", response_model=list[IssueSummaryResponse])
def list_issues_for_review(db: Session = Depends(get_db)):
    return list_operator_issues(db)


@router.get("/issues/{issue_id}", response_model=IssueResponse)
def get_issue_for_review(issue_id: int, db: Session = Depends(get_db)):
    return get_operator_issue(db, issue_id)


@router.patch("/issues/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    data: OperatorIssueUpdate,
    current_operator: User = Depends(get_current_operator),
    db: Session = Depends(get_db),
):
    return override_issue_decisions(db, issue_id, data)


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
