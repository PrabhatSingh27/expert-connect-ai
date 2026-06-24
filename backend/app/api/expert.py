from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User

from app.schemas.expert_profile import (
    ExpertProfileCreate,
    ExpertProfileResponse
)

router = APIRouter(
    prefix="/experts",
    tags=["Experts"]
)

from app.services.expert_profile_service import (
    create_expert_profile,
    get_my_profile,
    update_my_profile,
    get_all_experts,
    get_expert_by_id
)


@router.post(
    "/profile",
    response_model=ExpertProfileResponse
)
def create_profile(
    profile_data: ExpertProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_expert_profile(
        db,
        current_user.id,
        profile_data
    )

@router.get(
    "/profile/me",
    response_model=ExpertProfileResponse
)
def my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_my_profile(
        db,
        current_user.id
    )

from app.schemas.expert_profile import (
    ExpertProfileCreate,
    ExpertProfileUpdate,
    ExpertProfileResponse
)

@router.put(
    "/profile/me",
    response_model=ExpertProfileResponse
)
def update_profile(
    profile_data: ExpertProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_my_profile(
        db,
        current_user.id,
        profile_data
    )

@router.get(
    "/",
    response_model=list[ExpertProfileResponse]
)
def list_experts(
    db: Session = Depends(get_db)
):
    return get_all_experts(db)

@router.get(
    "/{expert_id}",
    response_model=ExpertProfileResponse
)
def expert_details(
    expert_id: int,
    db: Session = Depends(get_db)
):
    return get_expert_by_id(
        db,
        expert_id
    )