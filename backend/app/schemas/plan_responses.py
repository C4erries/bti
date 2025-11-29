"""Схемы для ответов API, связанных с 2D планами"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.plan import Plan


class Plan2DResponse(BaseModel):
    """Полный 2D план с геометрией для фронтенда"""
    orderId: uuid.UUID = Field(alias="orderId")
    versionType: str = Field(alias="versionType")
    versionId: uuid.UUID = Field(alias="versionId")
    plan: Plan
    comment: str | None = None
    createdAt: datetime | None = Field(default=None, alias="createdAt")
    createdBy: str | None = Field(default=None, alias="createdBy", description="Имя создателя версии")

    model_config = ConfigDict(populate_by_name=True)


class PlanBeforeAfterResponse(BaseModel):
    """Две версии плана для режима до/после"""
    original: Plan2DResponse | None = None
    modified: Plan2DResponse | None = None

    model_config = ConfigDict(populate_by_name=True)


class PlanDiffResponse(BaseModel):
    """Разница между версиями плана с подсветкой изменений"""
    original: Plan2DResponse | None = None
    modified: Plan2DResponse | None = None
    changes: dict = Field(
        default_factory=dict,
        description="Информация об изменениях: deleted (красный), added (зеленый), modified (желтый)"
    )

    model_config = ConfigDict(populate_by_name=True)


class PlanExportResponse(BaseModel):
    """Экспорт плана в JSON формате"""
    orderId: uuid.UUID = Field(alias="orderId")
    exportedAt: datetime = Field(alias="exportedAt")
    plan: Plan
    metadata: dict = Field(
        default_factory=dict,
        description="Дополнительная метаинформация: версия, автор, комментарий"
    )

    model_config = ConfigDict(populate_by_name=True)

