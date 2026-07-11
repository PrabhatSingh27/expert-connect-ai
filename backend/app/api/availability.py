from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_expert, get_db
from app.models.expert import Expert
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
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return create_availability(
        db,
        current_expert.id,
        data
    )

@router.get(
    "/me",
    response_model=list[AvailabilityResponse]
)
def my_availabilities(
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return get_my_availabilities(
        db,
        current_expert.id
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
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return update_availability(
        db,
        availability_id,
        current_expert.id,
        data
    )

@router.delete("/{availability_id}")
def remove_slot(
    availability_id: int,
    current_expert: Expert = Depends(get_current_expert),
    db: Session = Depends(get_db)
):
    return delete_availability(
        db,
        availability_id,
        current_expert.id
    )
