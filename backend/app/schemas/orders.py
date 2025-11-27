from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import AssignmentStatus, CalendarStatus, OrderStatus
from app.schemas.plan import Plan


class OrderFile(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID = Field(alias="orderId")
    sender_id: uuid.UUID | None = Field(default=None, alias="senderId")
    filename: str
    path: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OrderChatMessage(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID = Field(alias="chatId")
    order_id: uuid.UUID | None = Field(default=None, alias="orderId")
    sender_id: uuid.UUID | None = Field(default=None, alias="senderId")
    sender_type: str | None = Field(default=None, alias="senderType")
    message_text: str = Field(alias="messageText")
    meta: dict | None = None
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessagePairResponse(BaseModel):
    user_message: OrderChatMessage | None = Field(default=None, alias="userMessage")
    ai_message: OrderChatMessage | None = Field(default=None, alias="aiMessage")

    model_config = ConfigDict(populate_by_name=True)


class OrderPlanVersion(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID = Field(alias="orderId")
    version_type: str = Field(alias="versionType")
    plan: Plan

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SavePlanChangesRequest(BaseModel):
    version_type: str = Field(alias="versionType")
    plan: Plan

    model_config = ConfigDict(populate_by_name=True)


class AiRisk(BaseModel):
    type: str
    description: str
    severity: int | None = None
    zone: str | None = None


class AiAnalysis(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID = Field(alias="orderId")
    decision_status: str = Field(alias="decisionStatus")
    summary: str | None = None
    risks: list[AiRisk] | None = None
    legal_warnings: str | None = Field(default=None, alias="legalWarnings")
    financial_warnings: str | None = Field(default=None, alias="financialWarnings")
    raw_response: dict | None = Field(default=None, alias="rawResponse")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OrderStatusHistoryItem(BaseModel):
    old_status: str | None = Field(default=None, alias="oldStatus")
    status: str
    changed_by_user_id: uuid.UUID | None = Field(default=None, alias="changedByUserId")
    changed_at: datetime = Field(alias="changedAt")
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Order(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID = Field(alias="clientId")
    service_code: int = Field(alias="serviceCode")
    status: OrderStatus
    title: str
    description: str | None = None
    address: str | None = None
    district_code: str | None = Field(default=None, alias="districtCode")
    house_type_code: str | None = Field(default=None, alias="houseTypeCode")
    complexity: str | None = None
    calculator_input: dict | None = Field(default=None, alias="calculatorInput")
    estimated_price: float | None = Field(default=None, alias="estimatedPrice")
    total_price: float | None = Field(default=None, alias="totalPrice")
    current_department_code: str | None = Field(default=None, alias="currentDepartmentCode")
    ai_decision_status: str | None = Field(default=None, alias="aiDecisionStatus")
    ai_decision_summary: str | None = Field(default=None, alias="aiDecisionSummary")
    planned_visit_at: datetime | None = Field(default=None, alias="plannedVisitAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CreateOrderRequest(BaseModel):
    service_code: int = Field(alias="serviceCode")
    title: str
    description: str | None = None
    address: str | None = None
    district_code: str | None = Field(default=None, alias="districtCode")
    house_type_code: str | None = Field(default=None, alias="houseTypeCode")
    calculator_input: dict[str, Any] | None = Field(default=None, alias="calculatorInput")

    model_config = ConfigDict(populate_by_name=True)


class UpdateOrderRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    district_code: str | None = Field(default=None, alias="districtCode")
    house_type_code: str | None = Field(default=None, alias="houseTypeCode")
    calculator_input: dict[str, Any] | None = Field(default=None, alias="calculatorInput")

    model_config = ConfigDict(populate_by_name=True)


class AdminUpdateOrderRequest(BaseModel):
    status: OrderStatus | None = None
    current_department_code: str | None = Field(default=None, alias="currentDepartmentCode")
    estimated_price: float | None = Field(default=None, alias="estimatedPrice")
    total_price: float | None = Field(default=None, alias="totalPrice")

    model_config = ConfigDict(populate_by_name=True)


class ExecutorOrderListItem(BaseModel):
    id: uuid.UUID
    status: str
    service_title: str = Field(alias="serviceTitle")
    total_price: float | None = Field(default=None, alias="totalPrice")
    created_at: datetime = Field(alias="createdAt")
    complexity: str | None = None
    address: str | None = None
    department_code: str | None = Field(default=None, alias="departmentCode")

    model_config = ConfigDict(populate_by_name=True)


class ExecutorOrderDetails(BaseModel):
    order: Order
    files: list[OrderFile] | None = None
    plan_original: OrderPlanVersion | None = Field(default=None, alias="planOriginal")
    plan_modified: OrderPlanVersion | None = Field(default=None, alias="planModified")
    status_history: list[OrderStatusHistoryItem] = Field(default_factory=list, alias="statusHistory")
    client: User | None = None
    executor_assignment: dict | None = Field(default=None, alias="executorAssignment")

    model_config = ConfigDict(populate_by_name=True)


class AvailableSlot(BaseModel):
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    is_available: bool = Field(default=True, alias="isAvailable")

    model_config = ConfigDict(populate_by_name=True)


class ExecutorCalendarEvent(BaseModel):
    id: uuid.UUID
    executor_id: uuid.UUID = Field(alias="executorId")
    order_id: uuid.UUID | None = Field(default=None, alias="orderId")
    title: str | None = None
    description: str | None = None
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    location: str | None = None
    status: CalendarStatus
    created_at: datetime | None = Field(default=None, alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AssignExecutorRequest(BaseModel):
    executor_id: uuid.UUID = Field(alias="executorId")

    model_config = ConfigDict(populate_by_name=True)


class ScheduleVisitRequest(BaseModel):
    executor_id: uuid.UUID = Field(alias="executorId")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    location: str

    model_config = ConfigDict(populate_by_name=True)


class ScheduleVisitUpdateRequest(BaseModel):
    executor_id: uuid.UUID | None = Field(default=None, alias="executorId")
    start_time: datetime | None = Field(default=None, alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    status: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ExecutorScheduleVisitRequest(BaseModel):
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    location: str | None = None

    model_config = ConfigDict(populate_by_name=True)


from app.schemas.user import User  # noqa: E402

ExecutorOrderDetails.model_rebuild()
