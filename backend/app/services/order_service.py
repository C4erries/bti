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


def get_user_orders(db: Session, user_id: uuid.UUID) -> list[Order]:
    """Получить все заказы пользователя (как клиента и как исполнителя)"""
    # Заказы, где пользователь является клиентом
    client_orders = db.scalars(
        select(Order).where(Order.client_id == user_id)
    ).all()
    
    # Заказы, где пользователь является исполнителем
    executor_orders = db.scalars(
        select(Order)
        .join(ExecutorAssignment)
        .where(ExecutorAssignment.executor_id == user_id)
        .distinct()
    ).all()
    
    # Объединяем и убираем дубликаты
    all_orders = list(set(list(client_orders) + list(executor_orders)))
    
    # Сортируем по дате создания (новые первыми)
    all_orders.sort(key=lambda o: o.created_at, reverse=True)
    
    return all_orders


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


def list_admin_orders(
    db: Session,
    status: OrderStatus | str | None = None,
    executor_id: uuid.UUID | None = None,
    department_code: str | None = None,
) -> list[Order]:
    """Список заказов для админ-панели с фильтрами"""
    query = select(Order)
    
    if status:
        if isinstance(status, str):
            try:
                status_enum = OrderStatus(status)
            except ValueError:
                # Если статус не валидный, игнорируем фильтр
                status_enum = None
        else:
            status_enum = status
        if status_enum:
            query = query.where(Order.status == status_enum)
    
    if executor_id:
        # Используем exists для фильтрации по исполнителю, чтобы избежать проблем с join
        from sqlalchemy import exists
        query = query.where(
            exists().where(
                ExecutorAssignment.order_id == Order.id,
                ExecutorAssignment.executor_id == executor_id
            )
        )
    
    if department_code:
        # Фильтруем по отделу, но только если передан непустой код
        dept_code = department_code.strip() if isinstance(department_code, str) else str(department_code)
        if dept_code:
            query = query.where(Order.current_department_code == dept_code)
    
    try:
        orders_list = list(db.scalars(query.order_by(Order.created_at.desc())))
        return orders_list
    except Exception as e:
        # Логируем ошибку, но возвращаем пустой список вместо падения
        import traceback
        print(f"ERROR in list_admin_orders: {e}")
        print(traceback.format_exc())
        return []


def get_admin_order_details(db: Session, order_id: uuid.UUID) -> dict | None:
    """Получить детальную информацию о заказе для админ-панели"""
    try:
        order = get_order(db, order_id)
        if not order:
            return None
        
        # Клиент
        client = None
        try:
            client = user_service.get_user_by_id(db, order.client_id)
        except Exception as e:
            import traceback
            print(f"Error getting client for order {order_id}: {e}")
            print(traceback.format_exc())
        
        # Исполнитель
        executor = None
        executor_assignment = None
        try:
            assignment = db.scalar(
                select(ExecutorAssignment)
                .where(ExecutorAssignment.order_id == order_id)
                .order_by(ExecutorAssignment.assigned_at.desc())
                .limit(1)
            )
            if assignment:
                executor = user_service.get_user_by_id(db, assignment.executor_id)
                assignment_status = str(assignment.status)
                if hasattr(assignment.status, 'value'):
                    assignment_status = assignment.status.value
                executor_assignment = {
                    "id": str(assignment.id),
                    "executorId": str(assignment.executor_id),
                    "status": assignment_status,
                    "assignedAt": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                }
        except Exception as e:
            import traceback
            print(f"Error getting executor for order {order_id}: {e}")
            print(traceback.format_exc())
        
        # Файлы
        files = []
        try:
            files = list(db.scalars(select(OrderFile).where(OrderFile.order_id == order_id)))
        except Exception as e:
            import traceback
            print(f"Error getting files for order {order_id}: {e}")
            print(traceback.format_exc())
        
        # Версии планов
        plan_versions = []
        try:
            plan_versions = get_plan_versions(db, order_id)
        except Exception as e:
            import traceback
            print(f"Error getting plan versions for order {order_id}: {e}")
            print(traceback.format_exc())
        
        # История статусов
        status_history = []
        try:
            status_history = get_status_history(db, order_id)
        except Exception as e:
            import traceback
            print(f"Error getting status history for order {order_id}: {e}")
            print(traceback.format_exc())
        
        return {
            "order": order,
            "client": client,
            "executor": executor,
            "executorAssignment": executor_assignment,
            "files": files,
            "planVersions": plan_versions,
            "statusHistory": status_history,
        }
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in get_admin_order_details for order {order_id}: {e}")
        print(traceback.format_exc())
        return None


def admin_send_for_revision(db: Session, order: Order, admin: User, comment: str) -> OrderStatusHistory:
    """Отправить заказ на доработку"""
    # Переводим в статус SUBMITTED для повторной обработки
    return add_status_history(db, order, OrderStatus.SUBMITTED, admin, comment)


def admin_approve_order(db: Session, order: Order, admin: User, comment: str | None) -> OrderStatusHistory:
    """Утвердить заказ"""
    return add_status_history(db, order, OrderStatus.COMPLETED, admin, comment)


def admin_reject_order(db: Session, order: Order, admin: User, comment: str) -> OrderStatusHistory:
    """Отклонить заказ"""
    return add_status_history(db, order, OrderStatus.REJECTED, admin, comment)


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
        if order.current_department_code is None:
            order.current_department_code = executor.executor_profile.department_code
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
    db: Session, executor_id: uuid.UUID | None, status_filter: list[OrderStatus] | OrderStatus | None = None, department_code: str | None = None
) -> list[Order]:
    """
    Получить заказы исполнителя.
    Если executor_id = None (для суперадмина), возвращает все заказы с назначениями.
    """
    if executor_id is None:
        # Для суперадмина - все заказы с назначениями
        query = (
            select(Order)
            .join(ExecutorAssignment, ExecutorAssignment.order_id == Order.id)
            .where(ExecutorAssignment.status != AssignmentStatus.DECLINED)
        )
    else:
        # Для обычного исполнителя - только его заказы
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
    db: Session, order: Order, payload: SavePlanChangesRequest, created_by: User | None = None
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
        if payload.comment:
            existing.comment = payload.comment
        if created_by:
            existing.created_by_id = created_by.id
        db.add(existing)
        plan = existing
    else:
        plan = OrderPlanVersion(
            order_id=order.id,
            version_type=payload.version_type,
            plan=plan_data,
            is_applied=True,
            comment=payload.comment,
            created_by_id=created_by.id if created_by else None,
        )
        db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def executor_approve_plan(
    db: Session, order: Order, executor: User, comment: str | None = None
) -> OrderPlanVersion | None:
    """Одобрить план клиента - переводит в статус READY_FOR_APPROVAL"""
    # Находим текущий план (MODIFIED или ORIGINAL)
    current_plan = db.scalar(
        select(OrderPlanVersion)
        .where(OrderPlanVersion.order_id == order.id)
        .order_by(OrderPlanVersion.created_at.desc())
    )
    
    final_plan = None
    if current_plan:
        # Создаем финальную версию
        final_plan = OrderPlanVersion(
            order_id=order.id,
            version_type="FINAL",
            plan=current_plan.plan,
            is_applied=True,
            comment=comment or "План одобрен исполнителем",
            created_by_id=executor.id,
        )
        db.add(final_plan)
    
    add_status_history(db, order, OrderStatus.READY_FOR_APPROVAL, executor, comment)
    db.commit()
    if final_plan:
        db.refresh(final_plan)
    db.refresh(order)
    return final_plan


def executor_edit_plan(
    db: Session, order: Order, executor: User, plan_data: dict, comment: str
) -> OrderPlanVersion:
    """Отредактировать план - создает новую версию EXECUTOR_EDITED и отправляет клиенту на утверждение"""
    edited_plan = OrderPlanVersion(
        order_id=order.id,
        version_type="EXECUTOR_EDITED",
        plan=plan_data,
        is_applied=False,  # Не применена, ждет утверждения клиентом
        comment=comment,
        created_by_id=executor.id,
    )
    db.add(edited_plan)
    add_status_history(
        db, order, OrderStatus.AWAITING_CLIENT_APPROVAL, executor,
        f"План отредактирован исполнителем. {comment}"
    )
    db.commit()
    db.refresh(edited_plan)
    return edited_plan


def executor_reject_plan(
    db: Session, order: Order, executor: User, comment: str, issues: list[str] | None = None
) -> OrderStatusHistory:
    """Отклонить план - переводит в статус REJECTED_BY_EXECUTOR с комментарием и замечаниями"""
    rejection_comment = comment
    if issues:
        rejection_comment += f"\nЗамечания:\n" + "\n".join(f"- {issue}" for issue in issues)
    
    history = add_status_history(
        db, order, OrderStatus.REJECTED_BY_EXECUTOR, executor, rejection_comment
    )
    return history


def get_plan_versions(db: Session, order_id: uuid.UUID) -> list[OrderPlanVersion]:
    return list(
        db.scalars(
            select(OrderPlanVersion)
            .where(OrderPlanVersion.order_id == order_id)
            .order_by(OrderPlanVersion.created_at)
        )
    )


def get_status_history(db: Session, order_id: uuid.UUID) -> list[OrderStatusHistory]:
    """Получить историю статусов заказа с безопасной обработкой ошибок"""
    try:
        history = list(
            db.scalars(
                select(OrderStatusHistory)
                .where(OrderStatusHistory.order_id == order_id)
                .order_by(OrderStatusHistory.created_at)
            )
        )
        return history
    except Exception as e:
        import traceback
        print(f"Error getting status history for order {order_id}: {e}")
        print(traceback.format_exc())
        return []


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


def get_executor_calendar(db: Session, executor_id: uuid.UUID | None) -> list[ExecutorCalendarEvent]:
    """
    Получить календарь исполнителя.
    Если executor_id = None (для суперадмина), возвращает все события календаря.
    """
    if executor_id is None:
        # Для суперадмина - все события
        return list(db.scalars(select(ExecutorCalendarEvent)))
    else:
        # Для обычного исполнителя - только его события
        return list(
            db.scalars(
                select(ExecutorCalendarEvent).where(
                    ExecutorCalendarEvent.executor_id == executor_id
                )
            )
        )
