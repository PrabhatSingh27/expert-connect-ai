from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse
from app.services.auth_services import register_user
from app.database.session import SessionLocal
from fastapi import HTTPException

from app.auth.dependencies import get_current_account
from app.auth.dependencies import _ensure_user_can_authenticate
from app.models.user import User

from app.schemas.auth import (
    AuthMe,
    UserLogin,
    Token
)

from app.services.auth_services import (
    authenticate_user
)
from app.services.expert_service import expert_login

from app.core.security import (
    create_access_token
)
from app.core.rate_limit import rate_limit
from app.services.file_storage_service import save_upload_file
from app.utils.file_validator import validate_upload_file

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/register",
    response_model=UserResponse
)
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(..., min_length=1),
    photo: Optional[UploadFile] = File(None),
    _: None = Depends(rate_limit(limit=10, window_seconds=60)),
    db: Session = Depends(get_db)
):
    user = UserCreate(
        name=name,
        email=email,
        password=password,
        phone_number=phone_number,
    )
    if photo is not None and (photo.filename or photo.content_type):
        await validate_upload_file(photo, "image")
        user.profile_image_url = save_upload_file(photo, folder="profiles")
    return register_user(db, user)

@router.post(
    "/login",
    response_model=Token
)
def login(
    user_data: UserLogin,
    _: None = Depends(rate_limit(limit=10, window_seconds=60)),
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        user_data.email,
        user_data.password
    )

    if not user:
        return expert_login(db, user_data)

    _ensure_user_can_authenticate(user)

    normalized_role = (user.role or "customer").strip().lower()
    account_type = (
        "admin"
        if normalized_role == "admin"
        else "operator"
        if normalized_role == "operator"
        else "user"
    )

    token = create_access_token(
        {
            "sub": user.email,
            "role": normalized_role,
            "account_type": account_type,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": normalized_role,
        "account_type": account_type,
        "account_status": user.account_status,
        "is_expert": False,
        "is_admin": normalized_role == "admin",
        "is_verified": None,
        "name": user.name,
    }

@router.get(
    "/me",
    response_model=AuthMe
)
def get_me(
    current_account: dict = Depends(get_current_account)
):
    return current_account
