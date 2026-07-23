from datetime import datetime, timezone
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.expert import Expert
from app.models.issue import Issue
from app.models.user import User
from app.services.websocket_manager import publish_account_status_update, publish_issue_update


logger = logging.getLogger(__name__)


def list_users(db: Session):
    return db.query(User).all()


def list_experts(db: Session):
    return db.query(Expert).all()


def list_expert_applications(db: Session):
    return (
        db.query(Expert)
        .filter(Expert.is_verified.is_(False))
        .all()
    )


def list_issues(db: Session):
    return db.query(Issue).options(joinedload(Issue.assigned_expert)).all()


def _get_issue_with_assigned_expert(db: Session, issue_id: int) -> Issue | None:
    """Load the relation required by both the REST response and WS payload."""
    return (
        db.query(Issue)
        .options(joinedload(Issue.assigned_expert))
        .filter(Issue.id == issue_id)
        .first()
    )


def set_expert_verified(db: Session, expert_id: int, is_verified: bool):
    expert = db.query(Expert).filter(Expert.id == expert_id).first()
    if not expert:
        return None

    expert.is_verified = is_verified
    db.commit()
    db.refresh(expert)
    return expert


def set_user_active(db: Session, user_id: int, is_active: bool):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.is_active = is_active
    if is_active and getattr(user, "account_status", "active") in {"deactivated", "suspended"}:
        user.account_status = "active"
    db.commit()
    db.refresh(user)
    return user


def set_operator_suspension(db: Session, operator_id: int, suspended: bool):
    user = db.query(User).filter(User.id == operator_id).first()
    if not user:
        return None

    if (user.role or "").strip().lower() != "operator":
        raise ValueError("Target user is not an operator")

    user.account_status = "suspended" if suspended else "active"
    user.is_active = not suspended
    db.commit()
    db.refresh(user)
    publish_account_status_update(user)
    return user


def set_expert_active(db: Session, expert_id: int, is_active: bool):
    expert = db.query(Expert).filter(Expert.id == expert_id).first()
    if not expert:
        return None

    expert.is_active = is_active
    db.commit()
    db.refresh(expert)
    return expert


def get_analytics(db: Session):
    issues_by_status = dict(
        db.query(Issue.status, func.count(Issue.id))
        .group_by(Issue.status)
        .all()
    )

    return {
        "totalUsers": db.query(User).count(),
        "totalExperts": db.query(Expert).count(),
        "totalVerifiedExperts": db.query(Expert).filter(Expert.is_verified.is_(True)).count(),
        "totalIssues": db.query(Issue).count(),
        "issuesByStatus": issues_by_status,
    }


def override_issue_expert(db: Session, issue_id: int, expert_id: int):
    issue = _get_issue_with_assigned_expert(db, issue_id)
    if not issue:
        return None

    expert = db.query(Expert).filter(Expert.id == expert_id).first()
    if not expert:
        return None

    previous_expert_id = issue.assigned_expert_id
    issue.assigned_expert_id = expert.id
    issue.assigned_at = datetime.now(timezone.utc)
    issue.status = "in_progress"
    issue.admin_override_at = datetime.now(timezone.utc)

    db.commit()
    # Reload with the relationship eagerly populated.  This prevents the API
    # response and live event from containing only assignedExpertId.
    issue = _get_issue_with_assigned_expert(db, issue_id)

    logger.info(
        "admin_override_issue_expert issue_id=%s previous_expert_id=%s new_expert_id=%s",
        issue.id,
        previous_expert_id,
        expert.id,
    )
    publish_issue_update(
        issue,
        "admin_override",
        previous_expert_id=previous_expert_id,
    )
    return issue


def override_issue_priority(db: Session, issue_id: int, priority: str | None, urgency: str | None):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        return None

    previous_priority = issue.priority
    previous_urgency = issue.urgency

    if priority is not None:
        issue.priority = priority
    if urgency is not None:
        issue.urgency = urgency
    issue.admin_override_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(issue)

    logger.info(
        "admin_override_issue_priority issue_id=%s previous_priority=%s new_priority=%s previous_urgency=%s new_urgency=%s",
        issue.id,
        previous_priority,
        issue.priority,
        previous_urgency,
        issue.urgency,
    )
    publish_issue_update(issue, "admin_override")
    return issue


def override_issue(
    db: Session,
    issue_id: int,
    assigned_expert_id: int | None = None,
    priority: str | None = None,
    urgency: str | None = None,
    status: str | None = None,
):
    issue = _get_issue_with_assigned_expert(db, issue_id)
    if not issue:
        return None

    previous_expert_id = issue.assigned_expert_id
    if assigned_expert_id is not None:
        expert = db.query(Expert).filter(Expert.id == assigned_expert_id).first()
        if not expert:
            return None
        issue.assigned_expert_id = expert.id
        issue.assigned_at = datetime.now(timezone.utc)

    if priority is not None:
        issue.priority = priority
    if urgency is not None:
        issue.urgency = urgency
    if status is not None:
        issue.status = status
    issue.admin_override_at = datetime.now(timezone.utc)

    db.commit()
    issue = _get_issue_with_assigned_expert(db, issue_id)
    publish_issue_update(
        issue,
        "admin_override",
        previous_expert_id=previous_expert_id if assigned_expert_id is not None else None,
    )
    return issue
