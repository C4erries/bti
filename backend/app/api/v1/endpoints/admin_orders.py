import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.models.order import (
    ExecutorAssignment,
    OrderFile,
    OrderPlanVersion,
    OrderStatus,
)
from app.schemas.orders import (
    AdminUpdateOrderRequest,
    AdminOrderDetails,
    AdminOrderListItem,
    AdminSendForRevisionRequest,
    AdminApproveOrderRequest,
    AdminRejectOrderRequest,
    AdminAddCommentRequest,
    AssignExecutorRequest,
    Order,
    OrderFile as OrderFileSchema,
    OrderPlanVersion as OrderPlanVersionSchema,
    OrderStatusHistoryItem,
    ScheduleVisitRequest,
    ScheduleVisitUpdateRequest,
    ExecutorCalendarEvent,
)
from app.services import order_service, user_service
from sqlalchemy import select, func

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/orders", response_model=list[AdminOrderListItem], summary="Список заказов (админ)")
def list_orders(
    status: str | None = Query(default=None, description="Фильтр по статусу"),
    executorId: str | None = Query(default=None, description="Фильтр по исполнителю (UUID)"),
    departmentCode: str | None = Query(default=None, description="Фильтр по отделу"),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[AdminOrderListItem]:
    """Список заказов с фильтрами для админ-панели"""
    try:
        # Преобразуем executorId в UUID, если передан
        executor_uuid = None
        if executorId:
            try:
                executor_uuid = uuid.UUID(executorId)
            except (ValueError, TypeError):
                executor_uuid = None
        
        orders = order_service.list_admin_orders(db, status=status, executor_id=executor_uuid, department_code=departmentCode)
        
        result = []
        for order in orders:
            try:
                # Клиент
                client = user_service.get_user_by_id(db, order.client_id)
                
                # Исполнитель
                executor = None
                executor_comment = None
                try:
                    assignment = db.scalar(
                        select(ExecutorAssignment)
                        .where(ExecutorAssignment.order_id == order.id)
                        .order_by(ExecutorAssignment.assigned_at.desc())
                        .limit(1)
                    )
                    if assignment:
                        executor = user_service.get_user_by_id(db, assignment.executor_id)
                        # Получаем последний комментарий из истории статусов
                        from app.services.order_service import get_status_history
                        history = get_status_history(db, order.id)
                        if history:
                            executor_comment = history[-1].comment
                except Exception:
                    pass  # Игнорируем ошибки при получении исполнителя
                
                # Количество файлов
                files_count = 0
                try:
                    files_count = db.scalar(
                        select(func.count()).select_from(OrderFile).where(OrderFile.order_id == order.id)
                    ) or 0
                except Exception:
                    pass
                
                # Название услуги
                service_title = None
                try:
                    if order.service_code:
                        from app.models.directory import Service
                        service = db.get(Service, order.service_code)
                        if service:
                            service_title = service.name
                except Exception:
                    pass
                
                # Обработка статуса
                order_status = str(order.status)
                if hasattr(order.status, 'value'):
                    order_status = order.status.value
                
                result.append(AdminOrderListItem(
                    id=order.id,
                    status=order_status,
                    title=order.title or "",
                    description=order.description or None,
                    serviceCode=order.service_code,
                    serviceTitle=service_title,
                    clientId=order.client_id,
                    clientName=client.full_name if client else None,
                    executorId=executor.id if executor else None,
                    executorName=executor.full_name if executor else None,
                    currentDepartmentCode=order.current_department_code,
                    totalPrice=order.total_price,
                    filesCount=files_count,
                    createdAt=order.created_at,
                    plannedVisitAt=order.planned_visit_at,
                    completedAt=order.completed_at,
                    executorComment=executor_comment,
                ))
            except Exception as e:
                # Логируем ошибку для конкретного заказа, но продолжаем обработку остальных
                import traceback
                print(f"ERROR processing order {order.id}: {e}")
                print(traceback.format_exc())
                # Все равно добавляем заказ с минимальными данными
                try:
                    order_status = str(order.status)
                    if hasattr(order.status, 'value'):
                        order_status = order.status.value
                    result.append(AdminOrderListItem(
                        id=order.id,
                        status=order_status,
                        title=order.title or "",
                        description=order.description or None,
                        serviceCode=order.service_code,
                        serviceTitle=None,
                        clientId=order.client_id,
                        clientName=None,
                        executorId=None,
                        executorName=None,
                        currentDepartmentCode=order.current_department_code,
                        totalPrice=order.total_price,
                        filesCount=0,
                        createdAt=order.created_at,
                        plannedVisitAt=order.planned_visit_at,
                        completedAt=order.completed_at,
                        executorComment=None,
                    ))
                except Exception as e2:
                    print(f"CRITICAL: Failed to add order {order.id} even with minimal data: {e2}")
        
        return result
    except Exception as e:
        # Логируем общую ошибку
        import traceback
        print(f"CRITICAL ERROR in list_orders: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) from e


@router.get("/orders/{order_id}", response_model=AdminOrderDetails, summary="Детали заказа (админ)")
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> AdminOrderDetails:
    """Детальная информация о заказе для админ-панели"""
    try:
        details = order_service.get_admin_order_details(db, order_id)
        if not details:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Обрабатываем клиента
        client_schema = None
        if details.get("client"):
            try:
                from app.schemas.user import User
                client_obj = details["client"]
                if client_obj:
                    client_schema = User.model_validate(client_obj)
            except Exception as e:
                import traceback
                print(f"Error validating client: {e}")
                print(traceback.format_exc())
        
        # Обрабатываем исполнителя
        executor_schema = None
        if details.get("executor"):
            try:
                from app.schemas.user import User
                executor_obj = details["executor"]
                if executor_obj:
                    executor_schema = User.model_validate(executor_obj)
            except Exception as e:
                import traceback
                print(f"Error validating executor: {e}")
                print(traceback.format_exc())
        
        # Обрабатываем файлы
        files_list = []
        try:
            files_list = [OrderFileSchema.model_validate(f) for f in details.get("files", [])]
        except Exception as e:
            import traceback
            print(f"Error validating files: {e}")
            print(traceback.format_exc())
        
        # Обрабатываем версии планов
        plan_versions_list = []
        try:
            plan_versions_list = [OrderPlanVersionSchema.model_validate(v) for v in details.get("planVersions", [])]
        except Exception as e:
            import traceback
            print(f"Error validating plan versions: {e}")
            print(traceback.format_exc())
        
        # Обрабатываем историю статусов
        status_history_list = []
        try:
            status_history_list = [OrderStatusHistoryItem.model_validate(h) for h in details.get("statusHistory", [])]
        except Exception as e:
            import traceback
            print(f"Error validating status history: {e}")
            print(traceback.format_exc())
        
        return AdminOrderDetails(
            order=Order.model_validate(details["order"]),
            client=client_schema,
            executor=executor_schema,
            executorAssignment=details.get("executorAssignment"),
            files=files_list,
            planVersions=plan_versions_list,
            statusHistory=status_history_list,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in get_order: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) from e


@router.patch("/orders/{order_id}", response_model=Order, summary="Обновление заказа (админ)")
def update_order(
    order_id: uuid.UUID,
    data: AdminUpdateOrderRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    """Обновление заказа администратором: статус, цена, сроки, отдел"""
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
    
    if data.planned_visit_at is not None:
        order.planned_visit_at = data.planned_visit_at
    
    if data.completed_at is not None:
        order.completed_at = data.completed_at
    
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


@router.post("/orders/{order_id}/send-for-revision", response_model=Order, summary="Отправить заказ на доработку")
def send_for_revision(
    order_id: uuid.UUID,
    payload: AdminSendForRevisionRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    """Отправить заказ на доработку с комментарием"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.admin_send_for_revision(db, order, admin, payload.comment)
    db.refresh(order)
    return Order.model_validate(order)


@router.post("/orders/{order_id}/approve", response_model=Order, summary="Утвердить заказ")
def approve_order(
    order_id: uuid.UUID,
    payload: AdminApproveOrderRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    """Утвердить заказ"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.admin_approve_order(db, order, admin, payload.comment)
    db.refresh(order)
    return Order.model_validate(order)


@router.post("/orders/{order_id}/reject", response_model=Order, summary="Отклонить заказ")
def reject_order(
    order_id: uuid.UUID,
    payload: AdminRejectOrderRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    """Отклонить заказ с комментарием"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_service.admin_reject_order(db, order, admin, payload.comment)
    db.refresh(order)
    return Order.model_validate(order)


@router.post("/orders/{order_id}/comment", response_model=Order, summary="Добавить комментарий к заказу")
def add_comment(
    order_id: uuid.UUID,
    payload: AdminAddCommentRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> Order:
    """Добавить комментарий к заказу (без изменения статуса)"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Добавляем комментарий через историю статусов с текущим статусом
    order_service.add_status_history(db, order, order.status, admin, payload.comment)
    db.refresh(order)
    return Order.model_validate(order)


@router.get("/orders/{order_id}/plan/versions", response_model=list[OrderPlanVersionSchema], summary="Все версии плана заказа")
def get_all_plan_versions(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[OrderPlanVersionSchema]:
    """Получить все версии плана заказа для модерации"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    versions = order_service.get_plan_versions(db, order_id)
    return [OrderPlanVersionSchema.model_validate(v) for v in versions]
