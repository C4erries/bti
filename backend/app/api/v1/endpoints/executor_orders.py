import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.order import OrderStatus
from app.schemas.orders import (
    OrderFileRead,
    OrderRead,
    OrderStatusHistoryRead,
)
from app.services import order_service

router = APIRouter(prefix="/executor", tags=["executor-orders"])


def _ensure_executor(user):
    if not user.executor_profile:
        raise HTTPException(status_code=403, detail="Executor profile required")


@router.get("/orders", response_model=list[OrderRead])
def list_executor_orders(
    status: OrderStatus | None = Query(default=None),
    department_code: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderRead]:
    _ensure_executor(current_user)
    orders = order_service.get_executor_orders(db, current_user.id, status, department_code)
    return [OrderRead.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderRead:
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderRead.model_validate(order)


@router.post("/orders/{order_id}/take", response_model=OrderRead)
def take_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderRead:
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.executor_take_order(db, order, current_user)
    db.refresh(order)
    return OrderRead.model_validate(order)


@router.post("/orders/{order_id}/decline", response_model=OrderRead)
def decline_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderRead:
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.executor_decline_order(db, order, current_user)
    db.refresh(order)
    return OrderRead.model_validate(order)


@router.get("/orders/{order_id}/files", response_model=list[OrderFileRead])
def list_files(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderFileRead]:
    _ensure_executor(current_user)
    files = order_service.get_order_files(db, order_id)
    return [OrderFileRead.model_validate(f) for f in files]


@router.get("/orders/{order_id}/status-history", response_model=list[OrderStatusHistoryRead])
def list_status_history(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderStatusHistoryRead]:
    _ensure_executor(current_user)
    history = order_service.get_status_history(db, order_id)
    return [OrderStatusHistoryRead.model_validate(h) for h in history]
