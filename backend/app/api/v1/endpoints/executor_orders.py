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
    ExecutorApprovePlanRequest,
    ExecutorEditPlanRequest,
    ExecutorRejectPlanRequest,
    SavePlanChangesRequest,
    OrderPlanVersion,
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


@router.get("/orders/{order_id}/plan", response_model=OrderPlanVersion)
def get_order_plan(
    order_id: uuid.UUID,
    version: str | None = Query(default=None, description="ORIGINAL, MODIFIED, EXECUTOR_EDITED, FINAL"),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderPlanVersion:
    """Получить план заказа (для исполнителя)"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    versions = order_service.get_plan_versions(db, order_id)
    if version:
        match = next((v for v in versions if v.version_type.upper() == version.upper()), None)
        if match:
            return OrderPlanVersion.model_validate(match)
        raise HTTPException(status_code=404, detail=f"Plan version {version} not found")
    
    # По умолчанию возвращаем последнюю версию
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    return OrderPlanVersion.model_validate(versions[-1])


@router.get("/orders/{order_id}/plan/versions", response_model=list[OrderPlanVersion])
def get_all_plan_versions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderPlanVersion]:
    """Получить все версии плана заказа"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    versions = order_service.get_plan_versions(db, order_id)
    return [OrderPlanVersion.model_validate(v) for v in versions]


@router.post("/orders/{order_id}/plan/approve", response_model=ExecutorOrderDetails)
def approve_plan(
    order_id: uuid.UUID,
    payload: ExecutorApprovePlanRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExecutorOrderDetails:
    """Одобрить план клиента - переводит в статус READY_FOR_APPROVAL"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_service.executor_approve_plan(db, order, current_user, payload.comment)
    db.refresh(order)
    return get_order(order_id, db, current_user)


@router.post("/orders/{order_id}/plan/edit", response_model=ExecutorOrderDetails)
def edit_plan(
    order_id: uuid.UUID,
    payload: ExecutorEditPlanRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExecutorOrderDetails:
    """Отредактировать план - создает версию EXECUTOR_EDITED и отправляет клиенту на утверждение"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    plan_data = payload.plan.model_dump() if hasattr(payload.plan, 'model_dump') else payload.plan
    order_service.executor_edit_plan(db, order, current_user, plan_data, payload.comment)
    db.refresh(order)
    return get_order(order_id, db, current_user)


@router.post("/orders/{order_id}/plan/reject", response_model=ExecutorOrderDetails)
def reject_plan(
    order_id: uuid.UUID,
    payload: ExecutorRejectPlanRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExecutorOrderDetails:
    """Отклонить план - переводит в статус REJECTED_BY_EXECUTOR с комментарием и замечаниями"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_service.executor_reject_plan(db, order, current_user, payload.comment, payload.issues)
    db.refresh(order)
    return get_order(order_id, db, current_user)


@router.post("/orders/{order_id}/plan/save", response_model=OrderPlanVersion)
def save_plan_changes(
    order_id: uuid.UUID,
    payload: SavePlanChangesRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderPlanVersion:
    """Сохранить изменения плана (для редактора)"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    version = order_service.add_plan_version(db, order, payload, created_by=current_user)
    return OrderPlanVersion.model_validate(version)
