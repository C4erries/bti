import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas.orders import (
    OrderCreate,
    OrderRead,
    OrderUpdate,
    OrderFileRead,
    OrderPlanVersionRead,
    OrderStatusHistoryRead,
    PlanChangeRequest,
)
from app.services import order_service

router = APIRouter(prefix="/client", tags=["client-orders"])


def _ensure_ownership(order, user_id: uuid.UUID):
    if order.client_id != user_id:
        raise HTTPException(status_code=403, detail="Not your order")


@router.get("/orders", response_model=list[OrderRead])
def list_client_orders(
    db: Session = Depends(get_db_session), current_user=Depends(get_current_user)
) -> list[OrderRead]:
    orders = order_service.get_client_orders(db, current_user.id)
    return [OrderRead.model_validate(o) for o in orders]


@router.post("/orders", response_model=OrderRead, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderRead:
    order = order_service.create_order(db, current_user, payload)
    return OrderRead.model_validate(order)


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderRead:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    return OrderRead.model_validate(order)


@router.patch("/orders/{order_id}", response_model=OrderRead)
def update_order(
    order_id: uuid.UUID,
    payload: OrderUpdate,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderRead:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    order = order_service.update_order_by_client(db, order, payload)
    return OrderRead.model_validate(order)


@router.post("/orders/{order_id}/files", response_model=OrderFileRead)
def upload_file(
    order_id: uuid.UUID,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderFileRead:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    file = order_service.add_file(db, order, upload, uploaded_by=current_user)
    return OrderFileRead.model_validate(file)


@router.get("/orders/{order_id}/files", response_model=list[OrderFileRead])
def get_files(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderFileRead]:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    files = order_service.get_order_files(db, order_id)
    return [OrderFileRead.model_validate(f) for f in files]


@router.get("/orders/{order_id}/plan", response_model=list[OrderPlanVersionRead])
def get_plan_versions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderPlanVersionRead]:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    versions = order_service.get_plan_versions(db, order_id)
    return [OrderPlanVersionRead.model_validate(v) for v in versions]


@router.post("/orders/{order_id}/plan/changes", response_model=OrderPlanVersionRead)
def add_plan_change(
    order_id: uuid.UUID,
    payload: PlanChangeRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderPlanVersionRead:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    version = order_service.add_plan_version(
        db, order, geometry=payload.geometry, notes=payload.notes, user=current_user
    )
    return OrderPlanVersionRead.model_validate(version)


@router.get("/orders/{order_id}/status-history", response_model=list[OrderStatusHistoryRead])
def get_status_history(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderStatusHistoryRead]:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    history = order_service.get_status_history(db, order_id)
    return [OrderStatusHistoryRead.model_validate(h) for h in history]
