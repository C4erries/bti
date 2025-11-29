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
    is_superadmin: bool = Field(alias="isSuperadmin")
    is_blocked: bool = Field(default=False, alias="isBlocked")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(alias="fullName")
    phone: str | None = None
    is_admin: bool = False
    is_superadmin: bool = False

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
    is_superadmin: bool | None = Field(default=None, alias="isSuperadmin")

    model_config = ConfigDict(populate_by_name=True)


class UpdateUserRequest(BaseModel):
    full_name: str | None = Field(default=None, alias="fullName")
    phone: str | None = None
    is_admin: bool | None = Field(default=None, alias="isAdmin")
    is_superadmin: bool | None = Field(default=None, alias="isSuperadmin")
    is_blocked: bool | None = Field(default=None, alias="isBlocked")

    model_config = ConfigDict(populate_by_name=True)


class ExecutorDetails(BaseModel):
    user: User
    executor_profile: dict | None = Field(default=None, alias="executorProfile")

    model_config = ConfigDict(populate_by_name=True)


ExecutorCreateRequest = RegisterExecutorRequest
UserUpdateAdmin = UpdateUserRequest
UserRead = User
UserDetail = ExecutorDetails


class ExecutorAnalytics(BaseModel):
    """Аналитика по исполнителю"""
    executor_id: uuid.UUID = Field(alias="executorId")
    full_name: str = Field(alias="fullName")
    email: EmailStr
    department_code: str | None = Field(default=None, alias="departmentCode")
    current_load: int = Field(alias="currentLoad", description="Текущие задачи")
    last_activity: datetime | None = Field(default=None, alias="lastActivity", description="Последняя активность")
    avg_completion_days: float | None = Field(default=None, alias="avgCompletionDays", description="Среднее время выполнения заказов (дни)")
    errors_rejections: int = Field(alias="errorsRejections", description="Ошибки/отказы")
    total_completed: int = Field(alias="totalCompleted", description="Всего выполнено заказов")
    total_assigned: int = Field(alias="totalAssigned", description="Всего назначено заказов")
    
    model_config = ConfigDict(populate_by_name=True)
