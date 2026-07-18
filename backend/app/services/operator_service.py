"""Operator review operations for AI-assisted issue triage."""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.expert import Expert
from app.models.issue import Issue
from app.services.matching_service import eligible_experts_for_issue
from app.services.websocket_manager import publish_issue_update


logger = logging.getLogger(__name__)


def list_operator_issues(db: Session) -> list[Issue]:
    """Return all issues so operators can review both assigned and queued work."""
    return (
        db.query(Issue)
        .options(joinedload(Issue.assigned_expert))
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .all()
    )


def get_operator_issue(db: Session, issue_id: int) -> Issue:
    issue = (
        db.query(Issue)
        .options(joinedload(Issue.assigned_expert))
        .filter(Issue.id == issue_id)
        .first()
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


def _eligible_expert_ids(db: Session, issue: Issue) -> set[int]:
    return {candidate["expert"].id for candidate in eligible_experts_for_issue(db, issue)}


def override_issue_decisions(db: Session, issue_id: int, data) -> Issue:
    """Apply an operator's optional triage and assignment corrections safely."""
    issue = get_operator_issue(db, issue_id)
    previous_expert_id = issue.assigned_expert_id
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Provide at least one override field")

    assigned_expert_id = update_data.pop("assigned_expert_id", None)
    if assigned_expert_id is not None:
        expert = db.query(Expert).filter(Expert.id == assigned_expert_id).first()
        if expert is None:
            raise HTTPException(status_code=404, detail="Expert not found")
        if not expert.is_active or not expert.is_verified:
            raise HTTPException(status_code=400, detail="Expert must be active and verified")

        # Apply classification changes before checking eligibility, so an
        # operator cannot assign an expert who does not fit the corrected triage.
        for field in ("problem_type", "category", "priority", "urgency", "operator_note"):
            if field in update_data:
                setattr(issue, field, update_data[field])

        if expert.id not in _eligible_expert_ids(db, issue):
            raise HTTPException(
                status_code=400,
                detail="Expert is not eligible for this issue's skills, service area, or availability",
            )

        issue.assigned_expert_id = expert.id
        issue.assigned_at = datetime.now(timezone.utc)
        if "status" not in update_data:
            issue.status = "assigned"
    else:
        for field in ("problem_type", "category", "priority", "urgency", "operator_note"):
            if field in update_data:
                setattr(issue, field, update_data[field])

    if "status" in update_data:
        issue.status = update_data["status"]

    try:
        db.commit()
        db.refresh(issue)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("operator_issue_override_failed issue_id=%s", issue_id)
        raise HTTPException(status_code=500, detail="Unable to save issue override") from exc

    publish_issue_update(
        issue,
        "operator_issue_updated",
        previous_expert_id=previous_expert_id if assigned_expert_id is not None else None,
    )
    return issue
