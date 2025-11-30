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
    comment: str | None = None
    created_by_id: uuid.UUID | None = Field(default=None, alias="createdById")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")


class SavePlanChangesRequest(BaseModel):
    version_type: str = Field(alias="versionType")
    plan: Plan
    comment: str | None = None  # Комментарий при сохранении изменений

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ParsePlanResultRequest(BaseModel):
    """Запрос на сохранение результата парсинга плана от нейронки"""
    file_id: uuid.UUID = Field(alias="fileId", description="ID загруженного файла, который обрабатывался")
    plan: Plan = Field(description="Результат парсинга - структурированный план")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Уверенность распознавания (0.0 - 1.0)"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Список ошибок или предупреждений при распознавании"
    )
    processing_time_ms: int | None = Field(
        default=None,
        alias="processingTimeMs",
        description="Время обработки в миллисекундах"
    )

    model_config = ConfigDict(populate_by_name=True)


class ExecutorApprovePlanRequest(BaseModel):
    """Запрос на одобрение плана исполнителем"""
    comment: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ExecutorEditPlanRequest(BaseModel):
    """Запрос на редактирование плана исполнителем"""
    plan: Plan
    comment: str  # Обязательный комментарий с описанием изменений

    model_config = ConfigDict(populate_by_name=True)


class ExecutorRejectPlanRequest(BaseModel):
    """Запрос на отклонение плана исполнителем"""
    comment: str  # Обязательный комментарий с замечаниями
    issues: list[str] | None = None  # Список замечаний

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
    id: uuid.UUID
    order_id: uuid.UUID = Field(alias="orderId")
    status: str
    changed_by_id: uuid.UUID | None = Field(default=None, alias="changedByUserId")
    changed_by: dict | None = Field(default=None, alias="changedBy", description="Информация о пользователе, изменившем статус")
    created_at: datetime = Field(alias="changedAt")
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Order(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID = Field(alias="clientId")
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
    planned_visit_at: datetime | None = Field(default=None, alias="plannedVisitAt", description="Планируемая дата выезда")
    completed_at: datetime | None = Field(default=None, alias="completedAt", description="Дата завершения заказа")

    model_config = ConfigDict(populate_by_name=True)


class AdminOrderListItem(BaseModel):
    """Расширенная информация о заказе для админ-панели"""
    id: uuid.UUID
    status: str
    title: str
    description: str | None = None
    client_id: uuid.UUID = Field(alias="clientId")
    client_name: str | None = Field(default=None, alias="clientName")
    executor_id: uuid.UUID | None = Field(default=None, alias="executorId")
    executor_name: str | None = Field(default=None, alias="executorName")
    current_department_code: str | None = Field(default=None, alias="currentDepartmentCode")
    total_price: float | None = Field(default=None, alias="totalPrice")
    files_count: int = Field(default=0, alias="filesCount")
    created_at: datetime = Field(alias="createdAt")
    planned_visit_at: datetime | None = Field(default=None, alias="plannedVisitAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    executor_comment: str | None = Field(default=None, alias="executorComment", description="Последний комментарий исполнителя")

    model_config = ConfigDict(populate_by_name=True)


class AdminOrderDetails(BaseModel):
    """Детальная информация о заказе для админ-панели"""
    order: Order
    client: User | None = None
    executor: User | None = None
    executor_assignment: dict | None = Field(default=None, alias="executorAssignment")
    files: list[OrderFile] = Field(default_factory=list)
    plan_versions: list[OrderPlanVersion] = Field(default_factory=list, alias="planVersions")
    status_history: list[OrderStatusHistoryItem] = Field(default_factory=list, alias="statusHistory")

    model_config = ConfigDict(populate_by_name=True)


class AdminSendForRevisionRequest(BaseModel):
    """Запрос на отправку заказа на доработку"""
    comment: str  # Обязательный комментарий с указанием причин

    model_config = ConfigDict(populate_by_name=True)


class AdminApproveOrderRequest(BaseModel):
    """Запрос на утверждение заказа"""
    comment: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class AdminRejectOrderRequest(BaseModel):
    """Запрос на отклонение заказа"""
    comment: str  # Обязательный комментарий с причинами отклонения

    model_config = ConfigDict(populate_by_name=True)


class AdminAddCommentRequest(BaseModel):
    """Запрос на добавление комментария к заказу"""
    comment: str

    model_config = ConfigDict(populate_by_name=True)


class ExecutorOrderListItem(BaseModel):
    id: uuid.UUID
    status: str
    title: str
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


class RecognizePlanRequest(BaseModel):
    file_id: uuid.UUID = Field(alias="fileId")

    model_config = ConfigDict(populate_by_name=True)


from app.schemas.user import User  # noqa: E402

ExecutorOrderDetails.model_rebuild()
