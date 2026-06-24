from pydantic import BaseModel

class ExpertProfileCreate(BaseModel):
    title: str
    bio: str
    skills: str
    experience_years: int
    hourly_rate: int


class ExpertProfileResponse(BaseModel):
    id: int
    user_id: int
    title: str
    bio: str
    skills: str
    experience_years: int
    hourly_rate: int

    class Config:
        from_attributes = True

class ExpertProfileUpdate(BaseModel):
    title: str
    bio: str
    skills: str
    experience_years: int
    hourly_rate: int