from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.availability import Availability

def create_availability(
    db: Session,
    expert_id: int,
    data
):
    availability = Availability(
        expert_id=expert_id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time
    )

    db.add(availability)
    db.commit()
    db.refresh(availability)

    return availability

def get_my_availabilities(
    db,
    expert_id: int
):
    return (
        db.query(Availability)
        .filter(Availability.expert_id == expert_id)
        .all()
    )

def get_all_availabilities(db):
    return db.query(Availability).all()

def update_availability(
    db,
    availability_id: int,
    current_expert_id: int,
    data
):
    availability = (
        db.query(Availability)
        .filter(Availability.id == availability_id)
        .first()
    )

    if not availability:
        raise HTTPException(
            status_code=404,
            detail="Availability not found"
        )

    if availability.expert_id != current_expert_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    availability.day_of_week = data.day_of_week
    availability.start_time = data.start_time
    availability.end_time = data.end_time

    db.commit()
    db.refresh(availability)

    return availability

def delete_availability(
    db,
    availability_id: int,
    current_expert_id: int
):
    availability = (
        db.query(Availability)
        .filter(Availability.id == availability_id)
        .first()
    )

    if not availability:
        raise HTTPException(
            status_code=404,
            detail="Availability not found"
        )

    if availability.expert_id != current_expert_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    db.delete(availability)
    db.commit()

    return {
        "message": "Availability deleted"
    }
