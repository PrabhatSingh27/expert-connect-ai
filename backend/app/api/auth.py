from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse
from app.services.auth_services import register_user
from app.database.session import SessionLocal
from fastapi import HTTPException

from app.auth.dependencies import get_current_user
from app.models.user import User

from app.schemas.auth import (
    UserLogin,
    Token
)

from app.services.auth_services import (
    authenticate_user
)

from app.core.security import (
    create_access_token
)

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
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return register_user(db, user)

@router.post(
    "/login",
    response_model=Token
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        user_data.email,
        user_data.password
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "sub": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user