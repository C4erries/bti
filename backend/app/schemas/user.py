from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str = Field(alias="fullName")
    phone: str | None = None
    is_admin: bool = Field(alias="isAdmin")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(alias="fullName")
    phone: str | None = None
    is_admin: bool = False

    model_config = ConfigDict(populate_by_name=True)


class RegisterClientRequest(UserCreate):
    pass


class RegisterExecutorRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = Field(alias="fullName")
    phone: str | None = None
    department_code: str | None = Field(default=None, alias="departmentCode")
    experience_years: int | None = Field(default=None, alias="experienceYears")
    is_admin: bool | None = Field(default=None, alias="isAdmin")

    model_config = ConfigDict(populate_by_name=True)


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(default=None, alias="fullName")
    phone: str | None = None
    is_admin: bool | None = Field(default=None, alias="isAdmin")

    model_config = ConfigDict(populate_by_name=True)


class ExecutorDetails(BaseModel):
    user: User
    executor_profile: dict | None = Field(default=None, alias="executorProfile")

    model_config = ConfigDict(populate_by_name=True)


ExecutorCreateRequest = RegisterExecutorRequest
UserUpdateAdmin = UpdateUserRequest
UserRead = User
UserDetail = ExecutorDetails
