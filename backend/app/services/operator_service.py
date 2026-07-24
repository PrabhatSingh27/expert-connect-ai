"""Operator review operations for AI-assisted issue triage."""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.expert import Expert
from app.models.issue import Issue
from app.models.user import User
from app.services.matching_service import eligible_experts_for_issue
from app.services.websocket_manager import publish_issue_update


logger = logging.getLogger(__name__)


PRIMARY_OPERATOR_EMAIL = "op1@gmail.com"
OPERATOR_REVIEW_QUEUE_STATUSES = (
    "submitted",
    "ai_classified",
    "waiting_for_assignment",
    "pending_assignment",
    "operator_review",
    "need_more_info",
    "assigned",
    "in_progress",
)
OPEN_OPERATOR_STATUSES = ("assigned", "in_progress")


def get_primary_review_operator(db: Session) -> User | None:
    operator = (
        db.query(User)
        .filter(
            User.email == PRIMARY_OPERATOR_EMAIL,
            User.role == "operator",
            User.is_active.is_(True),
            User.account_status == "active",
        )
        .first()
    )
    if operator is not None:
        return operator

    return (
        db.query(User)
        .filter(
            User.role == "operator",
            User.is_active.is_(True),
            User.account_status == "active",
        )
        .order_by(User.id.asc())
        .first()
    )


def assign_primary_operator_review(db: Session, issue: Issue) -> User | None:
    """Set an active operator as review owner without changing expert assignment."""
    operator = get_primary_review_operator(db)
    if operator is None:
        logger.warning("operator_review_assignment_skipped issue_id=%s", getattr(issue, "id", None))
        return None
    issue.review_operator_id = operator.id
    return operator


def backfill_operator_review_assignments(
    db: Session,
    primary_operator_id: int,
    secondary_operator_id: int | None = None,
) -> int:
    """Assign missing or retired-operator review work to the primary operator."""
    conditions = [Issue.review_operator_id.is_(None)]
    if secondary_operator_id is not None:
        conditions.append(Issue.review_operator_id == secondary_operator_id)

    return (
        db.query(Issue)
        .filter(or_(*conditions))
        .update({Issue.review_operator_id: primary_operator_id}, synchronize_session=False)
    )


def list_operator_issues(db: Session, operator_id: int) -> list[Issue]:
    """Return only the authenticated operator's assigned review work."""
    return (
        db.query(Issue)
        .options(joinedload(Issue.assigned_expert))
        .filter(Issue.review_operator_id == operator_id)
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .all()
    )


def list_operator_queue(db: Session, operator_id: int) -> list[Issue]:
    """Return active review work owned by the authenticated operator."""
    return (
        db.query(Issue)
        .options(joinedload(Issue.assigned_expert))
        .filter(
            Issue.review_operator_id == operator_id,
            Issue.status.in_(OPERATOR_REVIEW_QUEUE_STATUSES),
        )
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .all()
    )


def get_operator_issue(
    db: Session,
    issue_id: int,
    operator_id: int,
    *,
    lock_for_update: bool = False,
) -> Issue:
    # PostgreSQL rejects ``FOR UPDATE`` on the nullable side of the OUTER JOIN
    # emitted by joinedload(Issue.assigned_expert). Lock only the Issue row;
    # response-only reads below may eager-load the expert relationship.
    query = db.query(Issue).filter(
        Issue.id == issue_id,
        Issue.review_operator_id == operator_id,
    )
    if lock_for_update:
        query = query.with_for_update(of=Issue)
    else:
        query = query.options(joinedload(Issue.assigned_expert))
    issue = query.first()
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


def _eligible_expert_ids(db: Session, issue: Issue) -> set[int]:
    return {candidate["expert"].id for candidate in eligible_experts_for_issue(db, issue)}


def override_issue_decisions(db: Session, issue_id: int, operator_id: int, data) -> Issue:
    """Apply an operator's optional triage and assignment corrections safely."""
    issue = get_operator_issue(db, issue_id, operator_id, lock_for_update=True)
    if getattr(issue, "admin_override_at", None) is not None:
        raise HTTPException(
            status_code=409,
            detail="Admin override is authoritative for this issue",
        )
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

        # An operator's deliberate selection is authoritative.  Availability,
        # location, and AI skill matching are recommendations, not a block on
        # human assignment.  The account must still be active and verified.
        for field in ("problem_type", "category", "priority", "urgency", "operator_note"):
            if field in update_data:
                setattr(issue, field, update_data[field])

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
        # Load the selected expert for the REST response and WebSocket payload
        # after the row lock has been released.
        issue = get_operator_issue(db, issue_id, operator_id)
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
