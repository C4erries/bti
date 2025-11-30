"""Pydantic-модели для рисков и анализа."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class AiRisk(BaseModel):
    """Модель риска, выявленного при анализе планировки."""
    type: Literal["TECHNICAL", "LEGAL", "FINANCIAL", "OPERATIONAL"] = Field(
        ...,
        description="Тип риска"
    )
    description: str = Field(..., description="Текстовое описание риска")
    severity: Optional[int] = Field(None, ge=1, le=5, description="Серьёзность риска по шкале 1–5")
    severity_str: Optional[Literal["low", "medium", "high", "critical"]] = Field(
        None,
        description="Серьёзность риска в текстовом формате"
    )
    zone: Optional[str] = Field(None, description="ID элемента на плане (например, wall_12, zone_1)")
    risk_id: Optional[str] = Field(None, description="Уникальный идентификатор риска")
    title: Optional[str] = Field(None, description="Краткое название риска")
    regulation_reference: Optional[str] = Field(None, description="Ссылка на нормативный документ")
    recommendation: Optional[str] = Field(None, description="Рекомендация по устранению риска")
    affected_elements: Optional[List[str]] = Field(None, description="Список ID затронутых элементов")
    alternative_suggestion: Optional[str] = Field(None, description="Предложение альтернативного решения")
    alts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Массив альтернативных вариантов планировки с геометрией (минимум 3, максимум 5 вариантов)"
    )

