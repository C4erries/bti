import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    is_admin: bool = False


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_admin: bool
    created_at: datetime


class ClientProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    organization_name: str | None = None
    is_legal_entity: bool = False
    notes: str | None = None


class ExecutorProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    department_code: str | None = None
    experience_years: int | None = None
    specialization: str | None = None


class UserDetail(UserRead):
    client_profile: ClientProfileRead | None = None
    executor_profile: ExecutorProfileRead | None = None


class UserUpdateAdmin(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    is_admin: bool | None = None


class ExecutorCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    department_code: str | None = None
    experience_years: int | None = None
    specialization: str | None = None
