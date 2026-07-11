from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expert import Expert
from app.models.issue import Issue
from app.models.user import User


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
    return db.query(Issue).all()


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
    db.commit()
    db.refresh(user)
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
