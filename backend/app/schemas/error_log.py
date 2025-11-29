"""Схемы для журнала ошибок"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.error_log import ErrorType, ErrorSeverity, ErrorStatus


class ErrorLogBase(BaseModel):
    """Базовая схема записи об ошибке"""
    error_type: ErrorType = Field(alias="errorType", description="Тип ошибки")
    input_data: dict | None = Field(default=None, alias="inputData", description="Входные данные")
    message: str = Field(description="Сообщение об ошибке")
    severity: ErrorSeverity = Field(default=ErrorSeverity.MEDIUM, description="Критичность")
    status: ErrorStatus = Field(default=ErrorStatus.NEW, description="Статус обработки")
    assigned_to_id: uuid.UUID | None = Field(default=None, alias="assignedToId", description="Ответственный")

    model_config = ConfigDict(populate_by_name=True)


class ErrorLogCreate(ErrorLogBase):
    """Схема для создания записи об ошибке"""
    pass


class ErrorLogUpdate(BaseModel):
    """Схема для обновления записи об ошибке"""
    status: ErrorStatus | None = None
    assigned_to_id: uuid.UUID | None = Field(default=None, alias="assignedToId")
    message: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ErrorLogRead(ErrorLogBase):
    """Схема для чтения записи об ошибке"""
    id: uuid.UUID
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    resolved_at: datetime | None = Field(default=None, alias="resolvedAt")
    assigned_to_name: str | None = Field(default=None, alias="assignedToName", description="Имя ответственного")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

