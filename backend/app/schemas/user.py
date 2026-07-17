from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str = Field(min_length=1)
    profile_image_url: str | None = None
    role: str = "customer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Profile fields a customer may change after registration."""

    name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    profile_image_url: str | None = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
