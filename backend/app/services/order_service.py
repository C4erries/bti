from pathlib import Path
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import (
    AssignmentStatus,
    ExecutorAssignment,
    ExecutorCalendarEvent,
    Order,
    OrderFile,
    OrderPlanVersion,
    OrderStatus,
    OrderStatusHistory,
)
from app.models.user import User
from app.schemas.orders import CreateOrderRequest, UpdateOrderRequest, SavePlanChangesRequest
from app.services import user_service
from app.services.price_calculator import calculate_order_price
from app.services.user_service import ensure_client_profile


def create_order(db: Session, client: User, data: CreateOrderRequest) -> Order:
    ensure_client_profile(db, client)
    calculator_data = data.calculator_input or {}
    order = Order(
        client_id=client.id,
        service_code=data.service_code,
        current_department_code=None,
        district_code=data.district_code,
        house_type_code=data.house_type_code,
        title=data.title,
        description=data.description,
        address=data.address,
        status=OrderStatus.SUBMITTED,
        calculator_input=calculator_data,
    )
    estimated, _ = calculate_order_price(db, order, calculator_data)
    order.estimated_price = estimated
    db.add(order)
    db.flush()
    history = OrderStatusHistory(
        order_id=order.id, status=order.status, changed_by_id=client.id
    )
    db.add(history)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: uuid.UUID) -> Order | None:
    return db.get(Order, order_id)


def get_client_orders(db: Session, client_id: uuid.UUID) -> list[Order]:
    return list(db.scalars(select(Order).where(Order.client_id == client_id)))


def update_order_by_client(db: Session, order: Order, data: UpdateOrderRequest) -> Order:
    if order.status not in (OrderStatus.DRAFT, OrderStatus.SUBMITTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order can be edited only in draft/submitted status",
        )
    for field in [
        "title",
        "description",
        "address",
        "district_code",
        "house_type_code",
    ]:
        value = getattr(data, field)
        if value is not None:
            setattr(order, field, value)
    if data.calculator_input is not None:
        order.calculator_input = data.calculator_input
    order.estimated_price, _ = calculate_order_price(db, order, order.calculator_input or {})
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def add_status_history(
    db: Session, order: Order, status_value: OrderStatus, user: User | None, comment: str | None = None
) -> OrderStatusHistory:
    order.status = status_value
    history = OrderStatusHistory(
        order_id=order.id,
        status=status_value,
        changed_by_id=user.id if user else None,
        comment=comment,
    )
    db.add(order)
    db.add(history)
    db.commit()
    db.refresh(order)
    db.refresh(history)
    return history


def list_admin_orders(db: Session) -> list[Order]:
    return list(db.scalars(select(Order)))


def assign_executor(
    db: Session, order: Order, executor: User, assigned_by: User | None = None
) -> ExecutorAssignment:
    assignment = ExecutorAssignment(
        order_id=order.id,
        executor_id=executor.id,
        assigned_by_id=assigned_by.id if assigned_by else None,
        status=AssignmentStatus.ASSIGNED,
    )
    if executor.executor_profile and executor.executor_profile.department_code:
        order.current_department_code = order.current_department_code or executor.executor_profile.department_code
    db.add(assignment)
    add_status_history(db, order, OrderStatus.EXECUTOR_ASSIGNED, assigned_by)
    db.refresh(assignment)
    return assignment


def executor_take_order(db: Session, order: Order, executor: User) -> ExecutorAssignment:
    assignment = (
        db.scalar(
            select(ExecutorAssignment).where(
                ExecutorAssignment.order_id == order.id,
                ExecutorAssignment.executor_id == executor.id,
            )
        )
        or assign_executor(db, order, executor, executor)
    )
    assignment.status = AssignmentStatus.ACCEPTED
    db.add(assignment)
    add_status_history(db, order, OrderStatus.EXECUTOR_ASSIGNED, executor)
    db.commit()
    db.refresh(assignment)
    return assignment


def executor_decline_order(db: Session, order: Order, executor: User) -> ExecutorAssignment:
    assignment = db.scalar(
        select(ExecutorAssignment).where(
            ExecutorAssignment.order_id == order.id,
            ExecutorAssignment.executor_id == executor.id,
        )
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.status = AssignmentStatus.DECLINED
    db.add(assignment)
    add_status_history(db, order, OrderStatus.REJECTED, executor)
    db.commit()
    db.refresh(assignment)
    return assignment


def get_executor_orders(
    db: Session, executor_id: uuid.UUID, status_filter: list[OrderStatus] | OrderStatus | None = None, department_code: str | None = None
) -> list[Order]:
    query = (
        select(Order)
        .join(ExecutorAssignment, ExecutorAssignment.order_id == Order.id)
        .where(
            ExecutorAssignment.executor_id == executor_id,
            ExecutorAssignment.status != AssignmentStatus.DECLINED,
        )
    )
    if status_filter:
        if isinstance(status_filter, list):
            query = query.where(Order.status.in_(status_filter))
        else:
            query = query.where(Order.status == status_filter)
    if department_code:
        query = query.where(Order.current_department_code == department_code)
    return list(db.scalars(query))


def add_file(db: Session, order: Order, file: UploadFile, uploaded_by: User | None = None) -> OrderFile:
    storage_dir = Path(settings.static_root) / "orders" / str(order.id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / file.filename
    content = file.file.read()
    file_path.write_bytes(content)
    path_value = f"{settings.static_url.rstrip('/')}/orders/{order.id}/{file.filename}"
    order_file = OrderFile(
        order_id=order.id,
        filename=file.filename,
        path=path_value,
        uploaded_by_id=uploaded_by.id if uploaded_by else None,
    )
    db.add(order_file)
    db.commit()
    db.refresh(order_file)
    return order_file


def get_order_files(db: Session, order_id: uuid.UUID) -> list[OrderFile]:
    return list(db.scalars(select(OrderFile).where(OrderFile.order_id == order_id)))


def add_plan_version(
    db: Session, order: Order, payload: SavePlanChangesRequest
) -> OrderPlanVersion:
    existing = db.scalar(
        select(OrderPlanVersion).where(
            OrderPlanVersion.order_id == order.id,
            OrderPlanVersion.version_type == payload.version_type,
        )
    )
    plan_data = payload.plan.model_dump()
    if existing:
        existing.plan = plan_data
        db.add(existing)
        plan = existing
    else:
        plan = OrderPlanVersion(
            order_id=order.id,
            version_type=payload.version_type,
            plan=plan_data,
            is_applied=True,
        )
        db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_plan_versions(db: Session, order_id: uuid.UUID) -> list[OrderPlanVersion]:
    return list(
        db.scalars(
            select(OrderPlanVersion)
            .where(OrderPlanVersion.order_id == order_id)
            .order_by(OrderPlanVersion.created_at)
        )
    )


def get_status_history(db: Session, order_id: uuid.UUID) -> list[OrderStatusHistory]:
    return list(
        db.scalars(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.created_at)
        )
    )


def create_calendar_event(
    db: Session,
    executor_id: uuid.UUID,
    order_id: uuid.UUID | None,
    start_time,
    end_time,
    location: str | None,
    notes: str | None,
) -> ExecutorCalendarEvent:
    event = ExecutorCalendarEvent(
        executor_id=executor_id,
        order_id=order_id,
        start_time=start_time,
        end_time=end_time,
        location=location,
        notes=notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def schedule_visit(
    db: Session,
    order: Order,
    executor_id: uuid.UUID,
    start_time,
    end_time,
    location: str | None = None,
) -> ExecutorCalendarEvent:
    executor = user_service.get_user_by_id(db, executor_id)
    if not executor or not executor.executor_profile:
        raise HTTPException(status_code=404, detail="Executor not found")
    order.planned_visit_at = start_time
    add_status_history(db, order, OrderStatus.VISIT_SCHEDULED, executor)
    db.add(order)
    event = create_calendar_event(
        db,
        executor_id=executor_id,
        order_id=order.id,
        start_time=start_time,
        end_time=end_time,
        location=location,
        notes=None,
    )
    return event


def update_visit(
    db: Session,
    order: Order,
    executor_id: uuid.UUID | None,
    start_time,
    end_time,
    status_value: str | None = None,
) -> ExecutorCalendarEvent | None:
    exec_id = executor_id
    if exec_id:
        executor = user_service.get_user_by_id(db, exec_id)
        if not executor or not executor.executor_profile:
            raise HTTPException(status_code=404, detail="Executor not found")
    else:
        assignment = db.scalar(
            select(ExecutorAssignment)
            .where(ExecutorAssignment.order_id == order.id)
            .order_by(ExecutorAssignment.assigned_at.desc())
        )
        exec_id = assignment.executor_id if assignment else None
    if exec_id is None:
        raise HTTPException(status_code=400, detail="Executor is required for visit")
    order.planned_visit_at = start_time or order.planned_visit_at
    db.add(order)
    event = create_calendar_event(
        db,
        executor_id=exec_id or order.client_id,
        order_id=order.id,
        start_time=start_time or order.planned_visit_at,
        end_time=end_time or start_time or order.planned_visit_at,
        location=None,
        notes=None,
    )
    if status_value:
        try:
            new_status = OrderStatus(status_value)
            add_status_history(db, order, new_status, None)
        except ValueError:
            pass
    return event


def get_executor_calendar(db: Session, executor_id: uuid.UUID) -> list[ExecutorCalendarEvent]:
    return list(
        db.scalars(
            select(ExecutorCalendarEvent).where(
                ExecutorCalendarEvent.executor_id == executor_id
            )
        )
    )
