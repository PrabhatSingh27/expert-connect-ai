from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserResponse
from app.services.auth_services import register_user
from app.database.session import SessionLocal
from fastapi import HTTPException

from app.auth.dependencies import get_current_account
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
    _: None = Depends(rate_limit(limit=10, window_seconds=60)),
    db: Session = Depends(get_db)
):
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

    normalized_role = (user.role or "customer").strip().lower()
    account_type = "admin" if normalized_role == "admin" else "user"

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
        "accessToken": token,
        "token": token,
        "tokenType": "bearer",
        "user_id": user.id,
        "userId": user.id,
        "role": normalized_role,
        "account_type": account_type,
        "accountType": account_type,
        "is_expert": False,
        "isExpert": False,
        "is_admin": normalized_role == "admin",
        "isAdmin": normalized_role == "admin",
        "is_verified": None,
        "isVerified": None,
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
