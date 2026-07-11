from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import create_review, get_expert_reviews

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.post("/issues/{issue_id}", response_model=ReviewResponse)
def submit_review(
    issue_id: int,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_review(db, issue_id, current_user.id, data)


@router.get("/experts/{expert_id}", response_model=list[ReviewResponse])
def expert_reviews(
    expert_id: int,
    db: Session = Depends(get_db),
):
    return get_expert_reviews(db, expert_id)
