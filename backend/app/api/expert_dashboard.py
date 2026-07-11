from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_expert, get_db
from app.models.expert import Expert
from app.schemas.issue import IssueResponse
from app.services.expert_service import get_completed_jobs, get_earnings

router = APIRouter(
    prefix="/expert",
    tags=["Expert Dashboard"],
)


@router.get("/jobs/completed", response_model=list[IssueResponse])
def completed_jobs(
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db),
):
    return get_completed_jobs(db, current_expert.id)


@router.get("/earnings")
def earnings(
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db),
):
    return get_earnings(db, current_expert.id)
