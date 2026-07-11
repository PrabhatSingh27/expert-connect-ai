from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.expert import Expert
from app.models.issue import Issue
from app.services.ai_classification_service import classify_issue_content
from app.services.file_storage_service import (
    delete_issue_attachments_from_storage,
    save_issue_media_groups,
)
from app.services.matching_service import match_experts_for_issue
from app.services.notification_service import notify_expert_assigned


ALLOWED_ISSUE_STATUSES = {
    "open",
    "ai_classified",
    "waiting_for_assignment",
    "assigned",
    "accepted",
    "in_progress",
    "resolved",
    "closed",
}


def _skills_to_text(skills) -> str | None:
    if skills is None:
        return None
    if isinstance(skills, list):
        return ", ".join(str(skill) for skill in skills if skill)
    return str(skills)


def create_issue(
    db: Session,
    customer_id: int,
    data,
    files=None,
    image_files=None,
    video_files=None,
    audio_files=None,
    audio_recordings=None,
):
    issue = Issue(
        customer_id=customer_id,
        title=data.title,
        description=data.description,
        problem_type=data.problem_type,
        category=data.category,
        priority=data.priority,
        urgency=data.urgency,
        required_skills=_skills_to_text(data.required_skills),
        preferred_visit_date=data.preferred_visit_date,
        preferred_time=data.preferred_time,
        location=data.location,
        pin_code=data.pin_code,
        address=data.address,
        image_path=data.image_path,
        video_path=data.video_path,
        audio_path=data.audio_path,
        status="open",
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    save_issue_media_groups(
        db,
        issue,
        image_files=image_files,
        video_files=video_files,
        audio_files=audio_files,
        audio_recordings=audio_recordings,
        files=files,
    )
    db.commit()
    db.refresh(issue)

    return issue


def get_all_issues(db: Session):
    return db.query(Issue).all()


def get_my_issues(db: Session, customer_id: int):
    return (
        db.query(Issue)
        .filter(Issue.customer_id == customer_id)
        .all()
    )


def get_issue_by_id(db: Session, issue_id: int):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )

    return issue


def get_customer_issue(db: Session, issue_id: int, customer_id: int):
    issue = get_issue_by_id(db, issue_id)

    if issue.customer_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    return issue


def update_issue(
    db: Session,
    issue_id: int,
    current_user_id: int,
    data,
    files=None,
    image_files=None,
    video_files=None,
    audio_files=None,
    audio_recordings=None,
):
    issue = get_customer_issue(db, issue_id, current_user_id)

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in ALLOWED_ISSUE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid issue status",
        )

    for field, value in update_data.items():
        if field == "required_skills":
            value = _skills_to_text(value)
        setattr(issue, field, value)

    save_issue_media_groups(
        db,
        issue,
        image_files=image_files,
        video_files=video_files,
        audio_files=audio_files,
        audio_recordings=audio_recordings,
        files=files,
    )
    db.commit()
    db.refresh(issue)

    return issue


def delete_issue(db: Session, issue_id: int, current_user_id: int):
    issue = get_customer_issue(db, issue_id, current_user_id)

    delete_issue_attachments_from_storage(issue)
    db.delete(issue)
    db.commit()

    return {"message": "Issue deleted successfully"}


def classify_issue(db: Session, issue_id: int, current_user_id: int):
    issue = get_customer_issue(db, issue_id, current_user_id)
    classification = classify_issue_content(issue)

    issue.category = classification["category"]
    issue.problem_type = classification["problem_type"]
    issue.priority = classification["priority"]
    issue.urgency = classification["urgency"]
    issue.required_skills = _skills_to_text(classification["required_skills"])
    issue.confidence_score = classification["confidence_score"]
    issue.ai_explanation = classification["ai_explanation"]
    issue.status = "ai_classified"

    db.commit()
    db.refresh(issue)

    return issue


def assign_best_expert(db: Session, issue_id: int, current_user_id: int):
    issue = get_customer_issue(db, issue_id, current_user_id)
    matches = match_experts_for_issue(db, issue, limit=1)

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="No matching experts found",
        )

    expert = db.query(Expert).filter(Expert.id == matches[0]["expert_id"]).first()
    if not expert:
        raise HTTPException(
            status_code=404,
            detail="Matched expert not found",
        )

    issue.assigned_expert_id = expert.id
    issue.assigned_at = datetime.now(timezone.utc)
    issue.status = "assigned"

    db.commit()
    db.refresh(issue)
    notify_expert_assigned(expert, issue)

    return issue
