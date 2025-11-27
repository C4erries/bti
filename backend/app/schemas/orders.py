import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.order import AssignmentStatus, CalendarStatus, OrderStatus


class OrderFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    url: str | None = None
    description: str | None = None
    uploaded_by_id: uuid.UUID | None = None
    created_at: datetime


class OrderPlanVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    geometry: dict | None = None
    notes: str | None = None
    is_applied: bool
    created_at: datetime


class OrderStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: OrderStatus
    comment: str | None = None
    changed_by_id: uuid.UUID | None = None
    created_at: datetime


class OrderChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender_id: uuid.UUID
    message: str
    created_at: datetime


class OrderBase(BaseModel):
    service_code: str
    title: str
    description: str | None = None
    address: str | None = None
    district_code: str | None = None
    house_type_code: str | None = None
    area: float | None = None
    calculator_input: dict[str, Any] | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    district_code: str | None = None
    house_type_code: str | None = None
    area: float | None = None
    calculator_input: dict[str, Any] | None = None


class OrderAdminUpdate(BaseModel):
    status: OrderStatus | None = None
    department_code: str | None = None
    estimated_price: float | None = None
    total_price: float | None = None
    ai_decision_status: str | None = None
    ai_decision_summary: str | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    service_code: str
    department_code: str | None
    district_code: str | None
    house_type_code: str | None
    title: str
    description: str | None
    address: str | None
    area: float | None
    status: OrderStatus
    calculator_input: dict | None
    estimated_price: float | None
    total_price: float | None
    ai_decision_status: str | None
    ai_decision_summary: str | None
    created_at: datetime
    updated_at: datetime
    files: list[OrderFileRead] = []
    plan_versions: list[OrderPlanVersionRead] = []
    status_history: list[OrderStatusHistoryRead] = []


class ExecutorAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    executor_id: uuid.UUID
    assigned_by_id: uuid.UUID | None = None
    status: AssignmentStatus
    assigned_at: datetime
    updated_at: datetime


class CalendarEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    executor_id: uuid.UUID
    order_id: uuid.UUID | None = None
    start_at: datetime
    end_at: datetime | None = None
    status: CalendarStatus
    location: str | None = None
    notes: str | None = None
    created_at: datetime


class PlanChangeRequest(BaseModel):
    geometry: dict | None = None
    notes: str | None = None
