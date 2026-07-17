from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.expert import Expert
from app.models.issue import Issue
from app.services.matching_service import eligible_experts_for_issue
from app.services.notification_service import notify_expert_assigned
from app.services.websocket_manager import publish_issue_update


def get_available_experts(db: Session, issue: Issue) -> list[Expert]:
    return [item["expert"] for item in eligible_experts_for_issue(db, issue)]


def assign_best_expert(
    issue: Issue,
    db: Session,
    *,
    commit: bool = True,
) -> Expert | None:
    """Assign the highest-ranked eligible expert using the shared fair matcher."""
    candidates = eligible_experts_for_issue(db, issue)
    if not candidates:
        return None

    selected_expert = candidates[0]["expert"]
    issue.assigned_expert_id = selected_expert.id
    issue.assigned_at = datetime.now(timezone.utc)
    issue.status = "assigned"

    if commit:
        db.commit()
        db.refresh(issue)
        notify_expert_assigned(selected_expert, issue)
        publish_issue_update(issue, "expert_assigned")

    return selected_expert


def assign_expert(db: Session, issue: Issue) -> Expert | None:
    return assign_best_expert(issue, db)


def get_expert_load(db: Session, expert_id: int) -> int:
    from app.models.issue import Issue

    return (
        db.query(Issue)
        .filter(
            Issue.assigned_expert_id == expert_id,
            Issue.status.in_(("assigned", "in_progress")),
        )
        .count()
    )
