import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: str
    password: str
    display_name: str | None = None
    timezone: str = "UTC"


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    timezone: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    timezone: str
    plan_tier: str
    is_active: bool
    created_at: datetime | None

    model_config = {"from_attributes": True}
