from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.expert import Expert
from app.models.issue import Issue
from app.services.notification_service import notify_issue_status_changed
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


def create_expert_account(db: Session, signup_data):
    full_name = (signup_data.full_name or "").strip()
    email = (signup_data.email or "").strip().lower()
    phone = (signup_data.phone or "").strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Full name is required"
        )

    if not email or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Valid email is required"
        )

    # Check email
    existing_expert = (
        db.query(Expert)
        .filter(Expert.email == email)
        .first()
    )

    if existing_expert:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check phone
    if not phone:
        phone = f"not-provided-{email}"

    existing_phone = db.query(Expert).filter(Expert.phone == phone).first()

    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered"
        )

    expert = Expert(
        full_name=full_name,
        email=email,
        phone=phone,
        government_id=signup_data.government_id or "",
        government_id_file_url=signup_data.government_id_file_url,
        skills=signup_data.skills or "",
        service_area=signup_data.service_area or "",
        service_city=signup_data.service_city,
        service_pincodes=signup_data.service_pincodes,
        bio=signup_data.bio,
        permanent_address=signup_data.permanent_address or "",
        profile_image_url=signup_data.profile_image_url,
        experience_years=signup_data.experience_years or 0,
        password_hash=hash_password(signup_data.password),
    )

    db.add(expert)
    db.commit()
    db.refresh(expert)

    return expert


def expert_login(db: Session, login_data):
    email = (login_data.email or "").strip().lower()

    expert = (
        db.query(Expert)
        .filter(Expert.email == email)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not expert.is_active:
        raise HTTPException(
            status_code=403,
            detail="Expert account is deactivated"
        )

    if not verify_password(
        login_data.password,
        expert.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(expert.id),
            "role": "expert",
            "account_type": "expert",
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expert_id": expert.id,
        "role": "expert",
        "account_type": "expert",
        "is_expert": True,
        "is_admin": False,
        "is_verified": expert.is_verified,
        "name": expert.full_name,
    }


def get_my_profile(db: Session, expert_id: int):
    expert = (
        db.query(Expert)
        .filter(Expert.id == expert_id)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=404,
            detail="Expert not found"
        )

    return expert


def update_my_profile(db: Session, expert_id: int, profile_data):
    expert = (
        db.query(Expert)
        .filter(Expert.id == expert_id)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=404,
            detail="Expert not found"
        )

    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expert, field, value)

    db.commit()
    db.refresh(expert)

    return expert


def get_all_experts(db: Session):
    return db.query(Expert).all()


def get_expert_by_id(db: Session, expert_id: int):
    expert = (
        db.query(Expert)
        .filter(Expert.id == expert_id)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=404,
            detail="Expert not found"
        )

    return expert


def get_expert_issues(db: Session, expert_id: int):
    return (
        db.query(Issue)
        .filter(Issue.assigned_expert_id == expert_id)
        .all()
    )


def get_expert_issue(db: Session, expert_id: int, issue_id: int):
    issue = (
        db.query(Issue)
        .filter(
            Issue.id == issue_id,
            Issue.assigned_expert_id == expert_id,
        )
        .first()
    )

    if not issue:
        raise HTTPException(
            status_code=404,
            detail="Issue not found",
        )

    return issue


def accept_issue(db: Session, expert_id: int, issue_id: int):
    issue = get_expert_issue(db, expert_id, issue_id)
    issue.status = "accepted"
    db.commit()
    db.refresh(issue)
    notify_issue_status_changed(issue, "accepted")
    return issue


def reject_issue(db: Session, expert_id: int, issue_id: int):
    issue = get_expert_issue(db, expert_id, issue_id)
    issue.status = "waiting_for_assignment"
    issue.assigned_expert_id = None
    issue.assigned_at = None
    db.commit()
    db.refresh(issue)
    notify_issue_status_changed(issue, "cancelled")
    return issue


def update_issue_status(db: Session, expert_id: int, issue_id: int, status: str):
    allowed_statuses = {
        "open",
        "ai_classified",
        "waiting_for_assignment",
        "assigned",
        "accepted",
        "in_progress",
        "resolved",
        "closed",
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid issue status",
        )

    issue = get_expert_issue(db, expert_id, issue_id)
    issue.status = status
    db.commit()
    db.refresh(issue)
    notify_issue_status_changed(issue, status)
    return issue


def get_completed_jobs(db: Session, expert_id: int):
    return (
        db.query(Issue)
        .filter(
            Issue.assigned_expert_id == expert_id,
            Issue.status.in_(["resolved", "closed"]),
        )
        .all()
    )


def get_earnings(db: Session, expert_id: int):
    completed_jobs = get_completed_jobs(db, expert_id)
    amount_per_job = 500

    return {
        "expert_id": expert_id,
        "completed_jobs": len(completed_jobs),
        "amount_per_job": amount_per_job,
        "total_earnings": len(completed_jobs) * amount_per_job,
        "currency": "INR",
    }
