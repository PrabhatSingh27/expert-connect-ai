from pydantic import BaseModel


class AvailabilityCreate(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str


class AvailabilityResponse(BaseModel):
    id: int
    expert_id: int
    day_of_week: str
    start_time: str
    end_time: str

    class Config:
        from_attributes = True
