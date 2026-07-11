from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    accessToken: str | None = None
    token: str | None = None
    tokenType: str | None = None
    user_id: int | None = None
    expert_id: int | None = None
    userId: int | None = None
    expertId: int | None = None
    role: str | None = None
    account_type: str | None = None
    accountType: str | None = None
    is_expert: bool = False
    isExpert: bool = False
    is_admin: bool = False
    isAdmin: bool = False
    is_verified: bool | None = None
    isVerified: bool | None = None
    name: str | None = None


class AuthMe(BaseModel):
    id: int
    user_id: int | None = None
    expert_id: int | None = None
    userId: int | None = None
    expertId: int | None = None
    email: str
    name: str
    role: str
    account_type: str
    accountType: str
    is_expert: bool
    isExpert: bool
    is_admin: bool = False
    isAdmin: bool = False
    is_verified: bool | None = None
    isVerified: bool | None = None
    is_active: bool = True
