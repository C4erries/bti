import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.types import GUID


class OrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EXECUTOR_ASSIGNED = "EXECUTOR_ASSIGNED"
    VISIT_SCHEDULED = "VISIT_SCHEDULED"
    DOCUMENTS_IN_PROGRESS = "DOCUMENTS_IN_PROGRESS"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"  # Готов к согласованию
    AWAITING_CLIENT_APPROVAL = "AWAITING_CLIENT_APPROVAL"  # Ожидает утверждения клиентом
    REJECTED_BY_EXECUTOR = "REJECTED_BY_EXECUTOR"  # Отклонён исполнителем
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"


class CalendarStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    current_department_code: Mapped[str | None] = mapped_column(String(50), ForeignKey("departments.code"))
    department_code: Mapped[str | None] = mapped_column(String(50), ForeignKey("departments.code"))
    district_code: Mapped[str | None] = mapped_column(String(50), ForeignKey("districts.code"))
    house_type_code: Mapped[str | None] = mapped_column(String(50), ForeignKey("house_types.code"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(String(255))
    area: Mapped[float | None] = mapped_column(Float)
    complexity: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False
    )
    calculator_input: Mapped[dict | None] = mapped_column(JSON, default=dict)
    estimated_price: Mapped[float | None] = mapped_column(Float)
    total_price: Mapped[float | None] = mapped_column(Float)
    ai_decision_status: Mapped[str | None] = mapped_column(String(100))
    ai_decision_summary: Mapped[str | None] = mapped_column(Text)
    planned_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    client: Mapped["User"] = relationship("User", back_populates="client_orders", foreign_keys=[client_id])
    department: Mapped["Department"] = relationship(
        "Department", foreign_keys=[current_department_code]
    )
    district: Mapped["District"] = relationship("District", back_populates="orders")
    house_type: Mapped["HouseType"] = relationship("HouseType", back_populates="orders")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory", back_populates="order", cascade="all, delete-orphan"
    )
    files: Mapped[list["OrderFile"]] = relationship(
        "OrderFile", back_populates="order", cascade="all, delete-orphan"
    )
    plan_versions: Mapped[list["OrderPlanVersion"]] = relationship(
        "OrderPlanVersion", back_populates="order", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["OrderChatMessage"]] = relationship(
        "OrderChatMessage", back_populates="order", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["ExecutorAssignment"]] = relationship(
        "ExecutorAssignment", back_populates="order", cascade="all, delete-orphan"
    )


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    order: Mapped[Order] = relationship("Order", back_populates="status_history")
    changed_by: Mapped["User"] = relationship("User")


class OrderFile(Base):
    __tablename__ = "order_files"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    order: Mapped[Order] = relationship("Order", back_populates="files")
    uploaded_by: Mapped["User"] = relationship("User")


class OrderPlanVersion(Base):
    __tablename__ = "order_plan_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    version_type: Mapped[str] = mapped_column(String(20))  # ORIGINAL / MODIFIED / EXECUTOR_EDITED
    plan: Mapped[dict] = mapped_column(JSON)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[str | None] = mapped_column(Text)  # Комментарий исполнителя при редактировании
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))  # Кто создал версию
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    order: Mapped[Order] = relationship("Order", back_populates="plan_versions")


class OrderChatMessage(Base):
    __tablename__ = "order_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("chat_threads.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id"))
    sender_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    sender_type: Mapped[str | None] = mapped_column(String(20))
    message_text: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    chat: Mapped["ChatThread"] = relationship("ChatThread", back_populates="messages")
    order: Mapped[Order] = relationship("Order", back_populates="chat_messages")
    sender: Mapped["User"] = relationship("User")


class ExecutorAssignment(Base):
    __tablename__ = "executor_assignments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    executor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    status: Mapped[AssignmentStatus] = mapped_column(Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    order: Mapped[Order] = relationship("Order", back_populates="assignments")
    executor: Mapped["User"] = relationship(
        "User", back_populates="executor_assignments", foreign_keys=[executor_id]
    )
    assigned_by: Mapped["User"] = relationship("User", foreign_keys=[assigned_by_id])


class ExecutorCalendarEvent(Base):
    __tablename__ = "executor_calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    executor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id"))
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[CalendarStatus] = mapped_column(Enum(CalendarStatus), default=CalendarStatus.PLANNED)
    location: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    executor: Mapped["User"] = relationship("User")
    order: Mapped["Order"] = relationship("Order")
