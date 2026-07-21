from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.issue import Issue
from app.services.assignment_service import assign_best_expert as assign_best_expert_to_issue
from app.services.ai_classification_service import classify_issue_content
from app.services.file_storage_service import (
    delete_issue_attachments_from_storage,
    save_issue_media_files,
)
from app.services.notification_service import notify_expert_assigned, notify_issue_status_changed
from app.services.operator_service import assign_primary_operator_review
from app.services.websocket_manager import publish_issue_update


ALLOWED_ISSUE_STATUSES = {
    "submitted",
    "ai_classified",
    "waiting_for_assignment",
    "operator_review",
    "need_more_info",
    "assigned",
    "in_progress",
    "completed",
    "closed",
}


def _skills_to_text(skills) -> str | None:
    if skills is None:
        return None
    if isinstance(skills, list):
        return ", ".join(str(skill) for skill in skills if skill)
    return str(skills)


def _apply_classification(issue: Issue, classification: dict) -> None:
    issue.category = classification["category"]
    issue.problem_type = classification["problem_type"]
    issue.priority = classification["priority"]
    issue.urgency = classification["urgency"]
    issue.required_skills = _skills_to_text(classification["required_skills"])
    issue.confidence_score = classification["confidence_score"]
    issue.ai_explanation = classification["ai_explanation"]
    issue.status = "ai_classified"


def create_issue(
    db: Session,
    customer_id: int,
    data,
    image=None,
    video=None,
    audio=None,
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
        status="submitted",
    )

    db.add(issue)
    # Allocate the ID before storage so media can be written beneath the
    # issue-specific directory; the following commit persists the submitted
    # issue together with its media paths.
    db.flush()

    save_issue_media_files(
        db,
        issue,
        image=image,
        video=video,
        audio=audio,
    )
    db.commit()
    db.refresh(issue)

    # The issue now has an ID and its stored media paths, so classify and assign
    # against the complete persisted record before making the final commit.
    classification = classify_issue_content(issue)
    _apply_classification(issue, classification)

    assigned_expert = assign_best_expert_to_issue(issue, db, commit=False)
    if assigned_expert is None:
        issue.status = "waiting_for_assignment"
    assign_primary_operator_review(db, issue)

    db.commit()
    db.refresh(issue)
    if assigned_expert is not None:
        notify_expert_assigned(assigned_expert, issue)
        publish_issue_update(issue, "expert_assigned")
    publish_issue_update(issue, "issue_created")

    return issue


def get_all_issues(db: Session):
    return db.query(Issue).options(joinedload(Issue.assigned_expert)).all()


def get_my_issues(db: Session, customer_id: int):
    return (
        db.query(Issue)
        .options(joinedload(Issue.assigned_expert))
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
    image=None,
    video=None,
    audio=None,
    allow_admin: bool = False,
):
    issue = get_issue_by_id(db, issue_id) if allow_admin else get_customer_issue(db, issue_id, current_user_id)

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

    save_issue_media_files(
        db,
        issue,
        image=image,
        video=video,
        audio=audio,
    )
    db.commit()
    db.refresh(issue)
    publish_issue_update(issue, "issue_updated")

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

    _apply_classification(issue, classification)

    db.commit()
    db.refresh(issue)

    return issue


def update_issue_status_any(db: Session, issue_id: int, status: str):
    if status not in ALLOWED_ISSUE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid issue status",
        )

    issue = get_issue_by_id(db, issue_id)
    issue.status = status
    db.commit()
    db.refresh(issue)
    notify_issue_status_changed(issue, status)
    publish_issue_update(issue, "issue_status_updated")
    return issue


def assign_best_expert_any(db: Session, issue_id: int):
    issue = get_issue_by_id(db, issue_id)
    expert = assign_best_expert_to_issue(issue, db, commit=False)
    if expert is None:
        raise HTTPException(
            status_code=404,
            detail="No eligible experts found",
        )

    db.commit()
    db.refresh(issue)
    notify_expert_assigned(expert, issue)
    publish_issue_update(issue, "expert_assigned")

    return issue


def assign_best_expert(db: Session, issue_id: int, current_user_id: int):
    issue = get_customer_issue(db, issue_id, current_user_id)
    expert = assign_best_expert_to_issue(issue, db, commit=False)
    if expert is None:
        raise HTTPException(
            status_code=404,
            detail="No eligible experts found",
        )

    db.commit()
    db.refresh(issue)
    notify_expert_assigned(expert, issue)
    publish_issue_update(issue, "expert_assigned")

    return issue
