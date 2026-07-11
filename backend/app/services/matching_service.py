from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.expert import Expert
from app.models.issue import Issue


def _text_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {
        token.strip().lower()
        for token in value.replace("|", ",").replace("/", ",").split(",")
        if token.strip()
    }


def _skill_score(issue: Issue, expert: Expert) -> int:
    required = _text_tokens(issue.required_skills or issue.category)
    expert_skills = _text_tokens(expert.skills)
    if not required:
        return 0
    return len(required.intersection(expert_skills)) * 40


def _service_area_score(issue: Issue, expert: Expert) -> int:
    if issue.pin_code and expert.service_pincodes:
        pincodes = _text_tokens(expert.service_pincodes)
        if issue.pin_code.strip().lower() in pincodes:
            return 30

    if issue.location and expert.service_city:
        if issue.location.strip().lower() in expert.service_city.strip().lower():
            return 20

    if issue.location and expert.service_area:
        if issue.location.strip().lower() in expert.service_area.strip().lower():
            return 20

    return 0


def _availability_score(db: Session, expert: Expert) -> int:
    has_slots = (
        db.query(Availability)
        .filter(Availability.expert_id == expert.id)
        .first()
        is not None
    )
    return 20 if has_slots else 0


def match_experts_for_issue(db: Session, issue: Issue, limit: int = 5) -> list[dict]:
    experts = (
        db.query(Expert)
        .filter(
            Expert.is_active.is_(True),
            Expert.is_verified.is_(True),
        )
        .all()
    )

    matches = []
    for expert in experts:
        score = (
            _skill_score(issue, expert)
            + _service_area_score(issue, expert)
            + _availability_score(db, expert)
            + min(expert.experience_years or 0, 10)
        )

        if score <= 0:
            continue

        matches.append(
            {
                "expert_id": expert.id,
                "full_name": expert.full_name,
                "skills": expert.skills,
                "service_area": expert.service_area,
                "score": score,
                "rating_sort_placeholder": None,
            }
        )

    return sorted(matches, key=lambda item: item["score"], reverse=True)[:limit]
