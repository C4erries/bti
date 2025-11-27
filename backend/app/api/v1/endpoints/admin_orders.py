import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.schemas.orders import (
    AdminUpdateOrderRequest,
    AssignExecutorRequest,
    Order,
    ScheduleVisitRequest,
    ScheduleVisitUpdateRequest,
    ExecutorCalendarEvent,
)
from app.services import order_service, user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/orders", response_model=list[Order], summary="Список заказов (админ)")
def list_orders(
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[Order]:
    orders = order_service.list_admin_orders(db)
    return [Order.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=Order, summary="Детали заказа (админ)")
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order.model_validate(order)


@router.patch("/orders/{order_id}", response_model=Order, summary="Обновление заказа (админ)")
def update_order(
    order_id: uuid.UUID,
    data: AdminUpdateOrderRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if data.status is not None:
        order_service.add_status_history(db, order, data.status, admin)
    if data.current_department_code is not None:
        order.current_department_code = data.current_department_code
    if data.estimated_price is not None:
        order.estimated_price = data.estimated_price
    if data.total_price is not None:
        order.total_price = data.total_price
    db.add(order)
    db.commit()
    db.refresh(order)
    return Order.model_validate(order)


@router.post("/orders/{order_id}/assign-executor", tags=["Admin"])
def assign_executor(
    order_id: uuid.UUID,
    payload: AssignExecutorRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    executor = user_service.get_user_by_id(db, payload.executor_id)
    if not executor or not executor.executor_profile:
        raise HTTPException(status_code=404, detail="Executor not found")
    order_service.assign_executor(db, order, executor, assigned_by=admin)
    db.refresh(order)
    return Order.model_validate(order)


@router.post("/orders/{order_id}/schedule-visit", tags=["Admin"], response_model=ExecutorCalendarEvent)
def schedule_visit(
    order_id: uuid.UUID,
    payload: ScheduleVisitRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    event = order_service.schedule_visit(
        db,
        order,
        executor_id=payload.executor_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        location=payload.location,
    )
    return ExecutorCalendarEvent.model_validate(event)


@router.patch("/orders/{order_id}/schedule-visit", tags=["Admin"], response_model=ExecutorCalendarEvent)
def update_visit(
    order_id: uuid.UUID,
    payload: ScheduleVisitUpdateRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    event = order_service.update_visit(
        db,
        order,
        executor_id=payload.executor_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status_value=payload.status,
    )
    return ExecutorCalendarEvent.model_validate(event)
