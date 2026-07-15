from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel


class AuthBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
    )


class UserLogin(AuthBaseModel):
    email: EmailStr
    password: str


class Token(AuthBaseModel):
    access_token: str
    token_type: str
    user_id: int | None = None
    expert_id: int | None = None
    role: str | None = None
    account_type: str | None = None
    is_expert: bool = False
    is_admin: bool = False
    is_verified: bool | None = None
    name: str | None = None


class AuthMe(AuthBaseModel):
    id: int
    user_id: int | None = None
    expert_id: int | None = None
    email: str
    name: str
    role: str
    account_type: str
    is_expert: bool
    is_admin: bool = False
    is_verified: bool | None = None
    is_active: bool = True
