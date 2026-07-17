from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator


class AvailabilityCreate(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, value: str) -> str:
        normalized = value.strip().lower()
        valid_days = {
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        }
        if normalized not in valid_days:
            raise ValueError("day_of_week must be a full weekday name")
        return normalized.capitalize()

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        normalized = value.strip().upper()
        for pattern in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I %p"):
            try:
                return datetime.strptime(normalized, pattern).strftime("%H:%M")
            except ValueError:
                continue
        raise ValueError("time must use HH:MM or H:MM AM/PM format")

    @model_validator(mode="after")
    def validate_time_range(self):
        start = datetime.strptime(self.start_time, "%H:%M").time()
        end = datetime.strptime(self.end_time, "%H:%M").time()
        if start >= end:
            raise ValueError("end_time must be later than start_time")
        return self


class AvailabilityResponse(BaseModel):
    id: int
    expert_id: int
    day_of_week: str
    start_time: str
    end_time: str

    class Config:
        from_attributes = True
