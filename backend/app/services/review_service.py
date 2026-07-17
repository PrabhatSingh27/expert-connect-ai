from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.expert_review import ExpertReview
from app.models.issue import Issue


def create_review(db: Session, issue_id: int, customer_id: int, data):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if issue.status not in {"completed", "closed"}:
        raise HTTPException(status_code=400, detail="Reviews can be submitted only after resolution")

    if not issue.assigned_expert_id:
        raise HTTPException(status_code=400, detail="Issue has no assigned expert")

    existing_review = (
        db.query(ExpertReview)
        .filter(
            ExpertReview.issue_id == issue_id,
            ExpertReview.customer_id == customer_id,
        )
        .first()
    )
    if existing_review:
        raise HTTPException(status_code=400, detail="Review already submitted")

    review = ExpertReview(
        issue_id=issue.id,
        expert_id=issue.assigned_expert_id,
        customer_id=customer_id,
        rating=data.rating,
        review=data.review,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


def get_expert_reviews(db: Session, expert_id: int):
    return (
        db.query(ExpertReview)
        .filter(ExpertReview.expert_id == expert_id)
        .all()
    )
