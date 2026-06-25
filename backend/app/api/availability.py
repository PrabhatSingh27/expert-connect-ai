from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityResponse
)
from app.services.availability_service import (
    create_availability,
    get_my_availabilities,
    get_all_availabilities,
    update_availability,
    delete_availability
)

router = APIRouter(
    prefix="/availability",
    tags=["Availability"]
)


@router.post(
    "/",
    response_model=AvailabilityResponse
)
def create_slot(
    data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_availability(
        db,
        current_user.id,
        data
    )

@router.get(
    "/me",
    response_model=list[AvailabilityResponse]
)
def my_availabilities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_my_availabilities(
        db,
        current_user.id
    )

@router.get(
    "/",
    response_model=list[AvailabilityResponse]
)
def list_availabilities(
    db: Session = Depends(get_db)
):
    return get_all_availabilities(db)

@router.put(
    "/{availability_id}",
    response_model=AvailabilityResponse
)
def update_slot(
    availability_id: int,
    data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_availability(
        db,
        availability_id,
        current_user.id,
        data
    )

@router.delete("/{availability_id}")
def remove_slot(
    availability_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_availability(
        db,
        availability_id,
        current_user.id
    )