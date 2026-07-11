from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.review import FeedbackCreate, ReviewResponse
from app.services.review_service import create_review

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
)


@router.post("/", response_model=ReviewResponse)
def submit_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_review(db, data.issue_id, current_user.id, data)
