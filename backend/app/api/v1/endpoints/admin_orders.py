import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.schemas.orders import AdminUpdateOrderRequest, Order
from app.services import order_service

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
