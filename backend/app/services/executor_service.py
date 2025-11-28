import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import AssignmentStatus, ExecutorAssignment
from app.models.order import ExecutorCalendarEvent, Order, OrderStatus, OrderStatusHistory
from app.models.user import ExecutorProfile, User
from app.schemas.user import ExecutorCreateRequest
from app.services import order_service, user_service


def create_executor(db: Session, data: ExecutorCreateRequest) -> User:
    return user_service.create_executor(db, data)


def list_executors(db: Session, department_code: str | None = None) -> list[ExecutorProfile]:
    query = select(ExecutorProfile)
    if department_code:
        query = query.where(ExecutorProfile.department_code == department_code)
    return list(db.scalars(query))


def get_executor_load(db: Session, executor_id) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ExecutorAssignment)
            .where(
                ExecutorAssignment.executor_id == executor_id,
                ExecutorAssignment.status != AssignmentStatus.DECLINED,
            )
        )
        or 0
    )


def get_calendar(db: Session, executor_id):
    return order_service.get_executor_calendar(db, executor_id)


def list_executors_by_department(db: Session, department_code: str | None) -> list[User]:
    query = (
        select(User)
        .join(ExecutorProfile, ExecutorProfile.user_id == User.id)
    )
    if department_code:
        query = query.where(ExecutorProfile.department_code == department_code)
    return list(db.scalars(query))


def get_executor_stats(db: Session, executor_id: uuid.UUID) -> dict:
    current_load = get_executor_load(db, executor_id)

    total_orders = (
        db.scalar(
            select(func.count(func.distinct(ExecutorAssignment.order_id))).where(
                ExecutorAssignment.executor_id == executor_id
            )
        )
        or 0
    )

    completed_orders = (
        db.scalar(
            select(func.count(func.distinct(Order.id)))
            .join(ExecutorAssignment, ExecutorAssignment.order_id == Order.id)
            .where(
                ExecutorAssignment.executor_id == executor_id,
                Order.status == OrderStatus.COMPLETED,
            )
        )
        or 0
    )

    avg_completion_days = db.scalar(
        select(
            func.avg(
                func.julianday(Order.completed_at) - func.julianday(Order.created_at)
            )
        )
        .join(ExecutorAssignment, ExecutorAssignment.order_id == Order.id)
        .where(
            ExecutorAssignment.executor_id == executor_id,
            Order.completed_at.is_not(None),
        )
    )
    if avg_completion_days is not None:
        avg_completion_days = float(avg_completion_days)

    assignments_subquery = select(ExecutorAssignment.order_id).where(
        ExecutorAssignment.executor_id == executor_id
    )

    last_status_activity = db.scalar(
        select(func.max(OrderStatusHistory.created_at)).where(
            OrderStatusHistory.order_id.in_(assignments_subquery)
        )
    )
    last_calendar_activity = db.scalar(
        select(func.max(ExecutorCalendarEvent.created_at)).where(
            ExecutorCalendarEvent.executor_id == executor_id
        )
    )
    last_assignment_activity = db.scalar(
        select(func.max(ExecutorAssignment.assigned_at)).where(
            ExecutorAssignment.executor_id == executor_id
        )
    )

    timestamps = [
        ts for ts in [last_status_activity, last_calendar_activity, last_assignment_activity] if ts
    ]
    last_activity_at: datetime | None = max(timestamps) if timestamps else None

    return {
        "current_load": current_load,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "avg_completion_days": avg_completion_days,
        "last_activity_at": last_activity_at,
    }
