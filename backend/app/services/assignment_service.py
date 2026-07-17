from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.expert import Expert
from app.models.issue import Issue
from app.services.notification_service import notify_expert_assigned
from app.services.websocket_manager import publish_issue_update


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        token.strip().lower()
        for token in value.replace("|", ",").replace("/", ",").split(",")
        if token.strip()
    }


def _matches_issue_category_or_skills(issue: Issue, expert: Expert) -> bool:
    issue_category = (issue.category or "").strip().lower()
    required_skills = _tokens(issue.required_skills)
    expert_skills = _tokens(expert.skills)
    expert_skills_text = (expert.skills or "").strip().lower()

    category_matches = bool(
        issue_category
        and (
            issue_category in expert_skills
            or issue_category in expert_skills_text
        )
    )
    skills_match = bool(required_skills.intersection(expert_skills))

    return category_matches or skills_match


def _supports_issue_pin_code(issue: Issue, expert: Expert) -> bool:
    if not issue.pin_code or not expert.service_pincodes:
        return False

    return issue.pin_code.strip().lower() in _tokens(expert.service_pincodes)


def _has_availability(db: Session, expert: Expert) -> bool:
    return (
        db.query(Availability.id)
        .filter(Availability.expert_id == expert.id)
        .first()
        is not None
    )


def get_available_experts(db: Session, issue: Issue) -> list[Expert]:
    experts = (
        db.query(Expert)
        .filter(
            Expert.is_active.is_(True),
            Expert.is_verified.is_(True),
        )
        .all()
    )

    return [
        expert
        for expert in experts
        if _matches_issue_category_or_skills(issue, expert)
        and _supports_issue_pin_code(issue, expert)
        and _has_availability(db, expert)
    ]


def assign_best_expert(
    issue: Issue,
    db: Session,
    *,
    commit: bool = True,
) -> Expert | None:
    """Assign the best available expert, optionally deferring the commit to a caller's pipeline."""
    experts = sorted(
        get_available_experts(db, issue),
        key=lambda expert: expert.experience_years or 0,
        reverse=True,
    )

    if not experts:
        return None

    selected_expert = experts[0]
    issue.assigned_expert_id = selected_expert.id
    issue.assigned_at = datetime.now(timezone.utc)
    issue.status = "assigned"

    if commit:
        db.commit()
        db.refresh(issue)
        notify_expert_assigned(selected_expert, issue)
        publish_issue_update(issue, "expert_assigned")

    return selected_expert


def assign_expert(db: Session, issue):
    return assign_best_expert(issue, db)


def get_expert_load(db: Session, expert_id: int):
    return (
        db.query(Issue)
        .filter(
            Issue.assigned_expert_id == expert_id,
            Issue.status.in_(["assigned", "in_progress"]),
        )
        .count()
    )
