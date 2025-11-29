"""Схемы для правил AI"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_rule import RiskType


class AIRuleBase(BaseModel):
    """Базовая схема правила AI"""
    name: str = Field(description="Название правила")
    trigger_condition: str = Field(alias="triggerCondition", description="Логическое условие срабатывания")
    risk_type: RiskType = Field(alias="riskType", description="Тип риска")
    description: str = Field(description="Описание риска для пользователя")
    severity: int = Field(ge=1, le=5, description="Серьезность риска (1-5)")
    risk_zone: str | None = Field(default=None, alias="riskZone", description="ID элемента на плане")
    is_enabled: bool = Field(default=True, alias="isEnabled", description="Включено/выключено")
    priority: int = Field(default=0, description="Приоритет правила")
    tags: list[str] = Field(default_factory=list, description="Теги для группировки")

    model_config = ConfigDict(populate_by_name=True)


class AIRuleCreate(AIRuleBase):
    """Схема для создания правила"""
    pass


class AIRuleUpdate(BaseModel):
    """Схема для обновления правила"""
    name: str | None = None
    trigger_condition: str | None = Field(default=None, alias="triggerCondition")
    risk_type: RiskType | None = Field(default=None, alias="riskType")
    description: str | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    risk_zone: str | None = Field(default=None, alias="riskZone")
    is_enabled: bool | None = Field(default=None, alias="isEnabled")
    priority: int | None = None
    tags: list[str] | None = None

    model_config = ConfigDict(populate_by_name=True)


class AIRuleRead(AIRuleBase):
    """Схема для чтения правила"""
    id: uuid.UUID
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AIRulePreviewRequest(BaseModel):
    """Запрос на предпросмотр ответа AI на основе правила"""
    test_scenario: dict = Field(alias="testScenario", description="Тестовый сценарий для проверки правила")

    model_config = ConfigDict(populate_by_name=True)


class AIRulePreviewResponse(BaseModel):
    """Ответ с предпросмотром AI"""
    rule_id: uuid.UUID = Field(alias="ruleId")
    rule_name: str = Field(alias="ruleName")
    would_trigger: bool = Field(alias="wouldTrigger", description="Сработает ли правило")
    preview_response: dict = Field(alias="previewResponse", description="Предпросмотр JSON ответа AI")

    model_config = ConfigDict(populate_by_name=True)


class AIRuleBatchActionRequest(BaseModel):
    """Запрос на массовое действие над правилами"""
    rule_ids: list[uuid.UUID] = Field(alias="ruleIds", description="ID правил")
    action: str = Field(description="Действие: enable, disable, add_tags, remove_tags")
    tags: list[str] | None = Field(default=None, description="Теги для действий с тегами")

    model_config = ConfigDict(populate_by_name=True)

