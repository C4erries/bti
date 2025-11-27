import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None
    is_admin: bool
    is_client: bool
    is_executor: bool
    created_at: datetime
    executor_department: str | None = None
