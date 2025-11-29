import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.types import GUID


class ErrorType(str, enum.Enum):
    """Тип ошибки"""
    AI_ERROR = "AI_ERROR"
    BACKEND_ERROR = "BACKEND_ERROR"
    PLAN_PROCESSING_ERROR = "PLAN_PROCESSING_ERROR"


class ErrorSeverity(str, enum.Enum):
    """Критичность ошибки"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ErrorStatus(str, enum.Enum):
    """Статус обработки ошибки"""
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class ErrorLog(Base):
    """Журнал ошибок системы"""
    __tablename__ = "error_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    error_type: Mapped[ErrorType] = mapped_column(Enum(ErrorType), nullable=False, index=True)
    input_data: Mapped[dict | None] = mapped_column(JSON, comment="Входные данные, которые привели к ошибке")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="Сообщение об ошибке")
    severity: Mapped[ErrorSeverity] = mapped_column(Enum(ErrorSeverity), nullable=False, default=ErrorSeverity.MEDIUM, index=True)
    status: Mapped[ErrorStatus] = mapped_column(Enum(ErrorStatus), nullable=False, default=ErrorStatus.NEW, index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), comment="Ответственный за обработку ошибки")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Дата решения ошибки"
    )

    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_id])

