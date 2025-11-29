import uuid
from datetime import datetime, timedelta
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session

from app.models.order import (
    AssignmentStatus,
    ExecutorAssignment,
    Order,
    OrderStatus,
)
from app.models.user import ExecutorProfile, User
from app.schemas.user import ExecutorCreateRequest, ExecutorAnalytics
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


def get_executor_analytics(
    db: Session, executor_id: uuid.UUID, department_code: str | None = None
) -> ExecutorAnalytics | None:
    """Получить аналитику по исполнителю"""
    executor = user_service.get_user_by_id(db, executor_id)
    if not executor or not executor.executor_profile:
        return None
    
    # Текущая нагрузка (активные заказы)
    current_load = get_executor_load(db, executor_id)
    
    # Последняя активность (последнее обновление назначения или заказа)
    last_assignment = db.scalar(
        select(ExecutorAssignment.updated_at)
        .where(ExecutorAssignment.executor_id == executor_id)
        .order_by(ExecutorAssignment.updated_at.desc())
        .limit(1)
    )
    
    last_order_update = db.scalar(
        select(Order.updated_at)
        .join(ExecutorAssignment, ExecutorAssignment.order_id == Order.id)
        .where(ExecutorAssignment.executor_id == executor_id)
        .order_by(Order.updated_at.desc())
        .limit(1)
    )
    
    last_activity = None
    if last_assignment and last_order_update:
        last_activity = max(last_assignment, last_order_update)
    elif last_assignment:
        last_activity = last_assignment
    elif last_order_update:
        last_activity = last_order_update
    
    # Среднее время выполнения заказов
    completed_assignments = db.scalars(
        select(ExecutorAssignment)
        .join(Order, ExecutorAssignment.order_id == Order.id)
        .where(
            ExecutorAssignment.executor_id == executor_id,
            Order.status == OrderStatus.COMPLETED,
            Order.completed_at.isnot(None),
            ExecutorAssignment.status == AssignmentStatus.ACCEPTED,
        )
        .order_by(ExecutorAssignment.assigned_at)
    ).all()
    
    avg_completion_days = None
    if completed_assignments:
        total_days = 0
        count = 0
        for assignment in completed_assignments:
            order = db.get(Order, assignment.order_id)
            if order and order.completed_at:
                days = (order.completed_at - assignment.assigned_at).total_seconds() / 86400
                if days > 0:
                    total_days += days
                    count += 1
        if count > 0:
            avg_completion_days = round(total_days / count, 1)
    
    # Ошибки/отказы (отклоненные назначения)
    errors_rejections = db.scalar(
        select(func.count())
        .select_from(ExecutorAssignment)
        .where(
            ExecutorAssignment.executor_id == executor_id,
            ExecutorAssignment.status == AssignmentStatus.DECLINED,
        )
    ) or 0
    
    # Всего выполнено
    total_completed = len(completed_assignments)
    
    # Всего назначено
    total_assigned = db.scalar(
        select(func.count())
        .select_from(ExecutorAssignment)
        .where(ExecutorAssignment.executor_id == executor_id)
    ) or 0
    
    return ExecutorAnalytics(
        executorId=executor.id,
        fullName=executor.full_name or "",
        email=executor.email,
        departmentCode=executor.executor_profile.department_code,
        currentLoad=current_load,
        lastActivity=last_activity,
        avgCompletionDays=avg_completion_days,
        errorsRejections=errors_rejections,
        totalCompleted=total_completed,
        totalAssigned=total_assigned,
    )


def list_executors_with_analytics(
    db: Session, department_code: str | None = None, search: str | None = None
) -> list[ExecutorAnalytics]:
    """Список исполнителей с аналитикой"""
    # Начинаем с профилей исполнителей, чтобы гарантировать наличие профиля
    query = select(ExecutorProfile).join(User, ExecutorProfile.user_id == User.id)
    
    # Применяем фильтры
    # Фильтр по отделу применяется строго, только если передан непустой код
    if department_code and isinstance(department_code, str):
        dept_filter = department_code.strip()
        if dept_filter:  # Применяем только если не пустая строка после strip
            query = query.where(ExecutorProfile.department_code == dept_filter)
    
    if search and isinstance(search, str):
        search_term = search.strip()
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )
    
    executor_profiles = db.scalars(query).all()
    
    analytics_list = []
    for profile in executor_profiles:
        # Получаем пользователя для этого профиля
        executor = db.get(User, profile.user_id)
        if executor:
            analytics = get_executor_analytics(db, executor.id, department_code)
            if analytics:
                analytics_list.append(analytics)
    
    return analytics_list
