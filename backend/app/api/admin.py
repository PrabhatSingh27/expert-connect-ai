from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin, get_db
from app.models.user import User
from app.schemas.admin import (
    AccountStatusUpdate,
    AnalyticsResponse,
    ExpertVerificationUpdate,
)
from app.schemas.expert import ExpertResponse
from app.schemas.issue import IssueSummaryResponse
from app.schemas.user import UserResponse
from app.services.admin_service import (
    get_analytics,
    list_experts,
    list_expert_applications,
    list_issues,
    list_users,
    set_expert_active,
    set_expert_verified,
    set_user_active,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/users", response_model=list[UserResponse])
def admin_list_users(db: Session = Depends(get_db)):
    return list_users(db)


@router.get("/experts", response_model=list[ExpertResponse])
def admin_list_experts(db: Session = Depends(get_db)):
    return list_experts(db)


@router.get("/experts/applications", response_model=list[ExpertResponse])
def admin_list_expert_applications(db: Session = Depends(get_db)):
    return list_expert_applications(db)


@router.get("/issues", response_model=list[IssueSummaryResponse])
def admin_list_issues(db: Session = Depends(get_db)):
    return list_issues(db)


@router.patch("/experts/{expert_id}/verify", response_model=ExpertResponse)
def verify_expert(
    expert_id: int,
    data: ExpertVerificationUpdate,
    db: Session = Depends(get_db),
):
    expert = set_expert_verified(db, expert_id, data.is_verified)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    data: AccountStatusUpdate,
    db: Session = Depends(get_db),
):
    user = set_user_active(db, user_id, data.is_active)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/experts/{expert_id}/status", response_model=ExpertResponse)
def update_expert_status(
    expert_id: int,
    data: AccountStatusUpdate,
    db: Session = Depends(get_db),
):
    expert = set_expert_active(db, expert_id, data.is_active)
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(db: Session = Depends(get_db)):
    return get_analytics(db)


@router.get("/overview", response_model=AnalyticsResponse)
def overview(db: Session = Depends(get_db)):
    return get_analytics(db)
