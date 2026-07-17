from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User
from app.models.expert import Expert
from app.core.security import SECRET_KEY, ALGORITHM


security = HTTPBearer()


def _decode_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


def _token_role(payload: dict) -> str:
    return str(
        payload.get("role")
        or payload.get("account_type")
        or payload.get("accountType")
        or ""
    ).strip().lower()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    payload = _decode_token(token)
    email = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated",
        )

    return user


def get_current_expert(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = _decode_token(token)
        expert_id = payload.get("sub")
        role = _token_role(payload)

        if expert_id is None or role != "expert":
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

        expert_id = int(expert_id)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    expert = (
        db.query(Expert)
        .filter(Expert.id == expert_id)
        .first()
    )

    if expert is None:
        raise HTTPException(
            status_code=401,
            detail="Expert not found",
        )

    if not expert.is_active:
        raise HTTPException(
            status_code=403,
            detail="Expert account is deactivated",
        )

    return expert


def get_current_admin(current_user: User = Depends(get_current_user)):
    if (current_user.role or "").strip().lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user


def get_current_operator(current_user: User = Depends(get_current_user)):
    if (current_user.role or "").strip().lower() != "operator":
        raise HTTPException(
            status_code=403,
            detail="Operator access required",
        )

    return current_user


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = _decode_token(credentials.credentials)
    role = _token_role(payload)
    subject = payload.get("sub")

    if not subject:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    if role == "expert":
        try:
            expert_id = int(subject)
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="Invalid expert token",
            )

        expert = db.query(Expert).filter(Expert.id == expert_id).first()
        if not expert:
            raise HTTPException(
                status_code=401,
                detail="Expert not found",
            )
        if not expert.is_active:
            raise HTTPException(
                status_code=403,
                detail="Expert account is deactivated",
            )

        return {
            "id": expert.id,
            "user_id": None,
            "expert_id": expert.id,
            "email": expert.email,
            "name": expert.full_name,
            "role": "expert",
            "account_type": "expert",
            "is_expert": True,
            "is_admin": False,
            "is_verified": expert.is_verified,
            "is_active": expert.is_active,
        }

    user = db.query(User).filter(User.email == subject).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated",
        )

    normalized_role = (user.role or "customer").strip().lower()
    account_type = (
        "admin"
        if normalized_role == "admin"
        else "operator"
        if normalized_role == "operator"
        else "user"
    )
    is_admin = normalized_role == "admin"
    return {
        "id": user.id,
        "user_id": user.id,
        "expert_id": None,
        "email": user.email,
        "name": user.name,
        "role": normalized_role,
        "account_type": account_type,
        "is_expert": False,
        "is_admin": is_admin,
        "is_verified": None,
        "is_active": user.is_active,
    }
