"""Pydantic-модели для запросов и ответов чат-бота."""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Модель для входящего сообщения чата."""
    role: str = Field(..., description="Роль отправителя: 'user' или 'assistant'")
    content: str = Field(..., description="Текст сообщения")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Временная метка сообщения")
    message_id: Optional[str] = Field(None, description="Уникальный идентификатор сообщения")


class ChatResponse(BaseModel):
    """Модель для ответа чат-бота."""
    content: str = Field(..., description="Текст ответа ассистента")
    message_id: Optional[str] = Field(None, description="Уникальный идентификатор ответа")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Временная метка ответа")
    sources: Optional[List[str]] = Field(None, description="Список источников информации, использованных для ответа")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Уровень уверенности ответа (0.0-1.0)")

