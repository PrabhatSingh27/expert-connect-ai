from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.file_storage_service import save_upload_file
from app.utils.file_validator import validate_upload_file


router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/profile/me", response_model=UserResponse)
async def update_my_profile(
    name: str | None = Form(None),
    email: EmailStr | None = Form(None),
    phone_number: str | None = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if name is not None:
        user.name = name
    if phone_number is not None:
        user.phone_number = phone_number
    if email is not None and str(email).lower() != user.email.lower():
        existing_user = (
            db.query(User)
            .filter(func.lower(User.email) == str(email).lower(), User.id != user.id)
            .first()
        )
        if existing_user is not None:
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = str(email)
    if photo is not None and (photo.filename or photo.content_type):
        await validate_upload_file(photo, "image")
        user.profile_image_url = save_upload_file(photo, folder="profiles")

    db.commit()
    db.refresh(user)
    return user
