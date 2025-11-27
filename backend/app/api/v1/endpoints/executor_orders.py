import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.order import OrderStatus
from app.schemas.orders import (
    ExecutorOrderListItem,
    ExecutorOrderDetails,
    OrderFile,
    OrderStatusHistoryItem,
    AvailableSlot,
    ExecutorScheduleVisitRequest,
    ScheduleVisitUpdateRequest,
    ExecutorCalendarEvent,
)
from app.services import order_service

router = APIRouter(prefix="/executor", tags=["Executor"])


def _ensure_executor(user):
    if not user.executor_profile:
        raise HTTPException(status_code=403, detail="Executor profile required")


@router.get("/orders", response_model=list[ExecutorOrderListItem])
def list_executor_orders(
    status: str | None = Query(default=None),
    department_code: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[ExecutorOrderListItem]:
    _ensure_executor(current_user)
    status_map = {
        "NEW": [OrderStatus.SUBMITTED, OrderStatus.EXECUTOR_ASSIGNED],
        "IN_PROGRESS": [OrderStatus.VISIT_SCHEDULED, OrderStatus.DOCUMENTS_IN_PROGRESS],
        "DONE": [OrderStatus.COMPLETED],
    }
    status_filters = status_map.get(status) if status else None
    orders = order_service.get_executor_orders(db, current_user.id, status_filters, department_code)
    return [
        ExecutorOrderListItem(
            id=o.id,
            status=o.status.value,
            serviceTitle=o.service.title if o.service else "",
            totalPrice=o.total_price,
            createdAt=o.created_at,
            complexity=o.complexity,
            address=o.address,
            departmentCode=o.current_department_code,
        )
        for o in orders
    ]


@router.get("/orders/{order_id}", response_model=ExecutorOrderDetails)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExecutorOrderDetails:
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    plan_original = next((p for p in order.plan_versions if p.version_type.upper() == "ORIGINAL"), None)
    plan_modified = next((p for p in order.plan_versions if p.version_type.upper() == "MODIFIED"), None)
    assignment = order.assignments[0] if order.assignments else None
    executor_assignment = (
        {
            "executorId": assignment.executor_id,
            "status": assignment.status.value if hasattr(assignment.status, "value") else assignment.status,
            "assignedAt": assignment.assigned_at,
            "assignedByUserId": assignment.assigned_by_id,
        }
        if assignment
        else None
    )
    return ExecutorOrderDetails(
        order=order,
        files=[OrderFile.model_validate(f) for f in order.files],
        planOriginal=plan_original,
        planModified=plan_modified,
        statusHistory=[OrderStatusHistoryItem.model_validate(h) for h in order.status_history],
        client=order.client,
        executorAssignment=executor_assignment,
    )


@router.post("/orders/{order_id}/take", response_model=ExecutorOrderDetails)
def take_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExecutorOrderDetails:
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.executor_take_order(db, order, current_user)
    db.refresh(order)
    return get_order(order_id, db, current_user)


@router.post("/orders/{order_id}/decline", response_model=ExecutorOrderDetails)
def decline_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExecutorOrderDetails:
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.executor_decline_order(db, order, current_user)
    db.refresh(order)
    return get_order(order_id, db, current_user)


@router.get("/orders/{order_id}/files", response_model=list[OrderFile])
def list_files(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderFile]:
    _ensure_executor(current_user)
    files = order_service.get_order_files(db, order_id)
    return [OrderFile.model_validate(f) for f in files]


@router.get("/orders/{order_id}/status-history", response_model=list[OrderStatusHistoryItem])
def list_status_history(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderStatusHistoryItem]:
    _ensure_executor(current_user)
    history = order_service.get_status_history(db, order_id)
    return [OrderStatusHistoryItem.model_validate(h) for h in history]


@router.get("/orders/{order_id}/available-slots", response_model=list[AvailableSlot])
def available_slots(
    order_id: uuid.UUID,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    _ensure_executor(current_user)
    # Stub available slots
    return []


@router.post("/orders/{order_id}/schedule-visit", response_model=ExecutorCalendarEvent)
def schedule_visit(
    order_id: uuid.UUID,
    payload: ExecutorScheduleVisitRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    event = order_service.schedule_visit(
        db,
        order,
        executor_id=current_user.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location,
    )
    return ExecutorCalendarEvent.model_validate(event)


@router.patch("/orders/{order_id}/schedule-visit", response_model=ExecutorCalendarEvent)
def update_visit(
    order_id: uuid.UUID,
    payload: ScheduleVisitUpdateRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    event = order_service.update_visit(
        db,
        order,
        executor_id=current_user.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status_value=payload.status,
    )
    return ExecutorCalendarEvent.model_validate(event)
