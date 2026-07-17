from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.expert import Expert
from app.models.issue import Issue


ACTIVE_ASSIGNMENT_STATUSES = ("assigned", "in_progress")


def _text_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        token.strip().lower()
        for token in value.replace("|", ",").replace("/", ",").split(",")
        if token.strip()
    }


def _matches_required_skills(issue: Issue, expert: Expert) -> bool:
    required_skills = _text_tokens(issue.required_skills)
    expert_skills = _text_tokens(expert.skills)
    category = (issue.category or "").strip().lower()
    expert_skills_text = (expert.skills or "").lower()

    if required_skills and required_skills.intersection(expert_skills):
        return True
    return bool(category and (category in expert_skills or category in expert_skills_text))


def _matches_service_area(issue: Issue, expert: Expert) -> bool:
    if issue.pin_code and expert.service_pincodes:
        return issue.pin_code.strip().lower() in _text_tokens(expert.service_pincodes)

    issue_location = (issue.location or "").strip().lower()
    if issue_location and expert.service_city:
        return issue_location in expert.service_city.strip().lower()
    if issue_location and expert.service_area:
        return issue_location in expert.service_area.strip().lower()

    # An expert without configured geographic restrictions may serve a location
    # that was not supplied by the customer.
    return not issue.pin_code and not issue_location


def _parse_time(value: str | None):
    if not value:
        return None
    normalized = value.strip().upper()
    for pattern in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(normalized, pattern).time()
        except ValueError:
            continue
    return None


def _is_available_for_issue(db: Session, issue: Issue, expert: Expert) -> bool:
    slots = db.query(Availability).filter(Availability.expert_id == expert.id).all()
    if not slots:
        return False

    if issue.preferred_visit_date is None:
        return True

    requested_day = issue.preferred_visit_date.strftime("%A").lower()
    day_slots = [slot for slot in slots if slot.day_of_week.strip().lower() == requested_day]
    if not day_slots:
        return False

    requested_time = _parse_time(issue.preferred_time)
    if requested_time is None:
        return True

    return any(
        (start := _parse_time(slot.start_time)) is not None
        and (end := _parse_time(slot.end_time)) is not None
        and start <= requested_time <= end
        for slot in day_slots
    )


def _candidate_loads(db: Session) -> dict[int, int]:
    rows = (
        db.query(Issue.assigned_expert_id, func.count(Issue.id))
        .filter(
            Issue.assigned_expert_id.is_not(None),
            Issue.status.in_(ACTIVE_ASSIGNMENT_STATUSES),
        )
        .group_by(Issue.assigned_expert_id)
        .all()
    )
    return {expert_id: count for expert_id, count in rows}


def _last_assignment_times(db: Session) -> dict[int, datetime]:
    rows = (
        db.query(Issue.assigned_expert_id, func.max(Issue.assigned_at))
        .filter(Issue.assigned_expert_id.is_not(None))
        .group_by(Issue.assigned_expert_id)
        .all()
    )
    return {expert_id: assigned_at for expert_id, assigned_at in rows if assigned_at is not None}


def eligible_experts_for_issue(db: Session, issue: Issue) -> list[dict]:
    """Return eligible experts with stable fairness metadata for one issue."""
    loads = _candidate_loads(db)
    last_assignments = _last_assignment_times(db)
    candidates = []

    for expert in (
        db.query(Expert)
        .filter(Expert.is_active.is_(True), Expert.is_verified.is_(True))
        .all()
    ):
        if not _matches_required_skills(issue, expert):
            continue
        if not _matches_service_area(issue, expert):
            continue
        if not _is_available_for_issue(db, issue, expert):
            continue

        load = loads.get(expert.id, 0)
        skill_score = 100
        location_score = 30 if issue.pin_code or issue.location else 0
        availability_score = 20
        experience_score = min(expert.experience_years or 0, 10)
        candidates.append(
            {
                "expert": expert,
                "load": load,
                "last_assigned_at": last_assignments.get(expert.id),
                "score": skill_score + location_score + availability_score + experience_score - (load * 10),
            }
        )

    # Least active work first provides load balancing.  The oldest assignment
    # then advances a deterministic round-robin position among equal-load peers.
    return sorted(
        candidates,
        key=lambda item: (
            item["load"],
            item["last_assigned_at"] is not None,
            item["last_assigned_at"] or datetime.min,
            -item["score"],
            item["expert"].id,
        ),
    )


def match_experts_for_issue(db: Session, issue: Issue, limit: int = 5) -> list[dict]:
    return [
        {
            "expert_id": item["expert"].id,
            "full_name": item["expert"].full_name,
            "skills": item["expert"].skills,
            "service_area": item["expert"].service_area,
            "score": item["score"],
            "active_assignment_count": item["load"],
            "last_assigned_at": item["last_assigned_at"],
        }
        for item in eligible_experts_for_issue(db, issue)[:limit]
    ]
