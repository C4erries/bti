import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.types import GUID


class RiskType(str, enum.Enum):
    """Тип риска для правил AI"""
    TECHNICAL = "TECHNICAL"
    LEGAL = "LEGAL"
    FINANCIAL = "FINANCIAL"
    OPERATIONAL = "OPERATIONAL"


class AIRule(Base):
    """Правило для AI-анализа планов перепланировки"""
    __tablename__ = "ai_rules"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    trigger_condition: Mapped[str] = mapped_column(Text, nullable=False, comment="Логическое условие срабатывания правила")
    risk_type: Mapped[RiskType] = mapped_column(Enum(RiskType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="Описание риска для пользователя")
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="Серьезность риска (1-5)")
    risk_zone: Mapped[str | None] = mapped_column(String(255), comment="ID элемента на плане, к которому привязан риск")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="Приоритет правила для разрешения конфликтов")
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=list, comment="Теги для группировки правил")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

