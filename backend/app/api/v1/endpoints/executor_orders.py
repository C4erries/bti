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
from app.schemas.plan_responses import (
    Plan2DResponse,
    PlanBeforeAfterResponse,
    PlanDiffResponse,
    PlanExportResponse,
)
from app.services import order_service

router = APIRouter(prefix="/executor", tags=["Executor"])


def _ensure_executor(user):
    """Проверка, что пользователь является исполнителем или суперадмином"""
    if user.is_superadmin:
        return  # Суперадмин имеет доступ ко всем методам
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
    # Для суперадмина получаем все заказы, для обычного исполнителя - только его заказы
    executor_id = None if current_user.is_superadmin else current_user.id
    orders = order_service.get_executor_orders(db, executor_id, status_filters, department_code)
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


@router.get("/orders/{order_id}/plan/2d", response_model=Plan2DResponse, summary="Получить 2D план с полной геометрией (исполнитель)")
def get_plan_2d_executor(
    order_id: uuid.UUID,
    version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> Plan2DResponse:
    """Получить 2D план с полной геометрией для исполнителя"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    versions = order_service.get_plan_versions(db, order_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Выбираем версию
    plan_version = None
    if version:
        match = next((v for v in versions if v.version_type.upper() == version.upper()), None)
        if match:
            plan_version = match
        else:
            raise HTTPException(status_code=404, detail=f"Plan version {version} not found")
    else:
        plan_version = versions[-1]  # Последняя версия
    
    # Получаем имя создателя
    created_by_name = None
    if plan_version.created_by_id:
        from app.services import user_service
        creator = user_service.get_user_by_id(db, plan_version.created_by_id)
        if creator:
            created_by_name = creator.full_name
    
    return Plan2DResponse(
        orderId=order_id,
        versionType=plan_version.version_type,
        versionId=plan_version.id,
        plan=plan_version.plan,
        comment=plan_version.comment,
        createdAt=plan_version.created_at,
        createdBy=created_by_name,
    )


@router.get("/orders/{order_id}/plan/before-after", response_model=PlanBeforeAfterResponse, summary="Получить план в режиме до/после (исполнитель)")
def get_plan_before_after_executor(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlanBeforeAfterResponse:
    """Получить две версии плана (ORIGINAL и MODIFIED) для режима до/после (исполнитель)"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    versions = order_service.get_plan_versions(db, order_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    original = None
    modified = None
    
    for v in versions:
        if v.version_type.upper() == "ORIGINAL":
            created_by_name = None
            if v.created_by_id:
                from app.services import user_service
                creator = user_service.get_user_by_id(db, v.created_by_id)
                if creator:
                    created_by_name = creator.full_name
            original = Plan2DResponse(
                orderId=order_id,
                versionType=v.version_type,
                versionId=v.id,
                plan=v.plan,
                comment=v.comment,
                createdAt=v.created_at,
                createdBy=created_by_name,
            )
        elif v.version_type.upper() in ["MODIFIED", "EXECUTOR_EDITED"]:
            created_by_name = None
            if v.created_by_id:
                from app.services import user_service
                creator = user_service.get_user_by_id(db, v.created_by_id)
                if creator:
                    created_by_name = creator.full_name
            modified = Plan2DResponse(
                orderId=order_id,
                versionType=v.version_type,
                versionId=v.id,
                plan=v.plan,
                comment=v.comment,
                createdAt=v.created_at,
                createdBy=created_by_name,
            )
    
    return PlanBeforeAfterResponse(original=original, modified=modified)


@router.get("/orders/{order_id}/plan/diff", response_model=PlanDiffResponse, summary="Получить разницу между версиями плана (исполнитель)")
def get_plan_diff_executor(
    order_id: uuid.UUID,
    original_version: str | None = None,
    modified_version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlanDiffResponse:
    """Получить разницу между версиями плана с подсветкой изменений (исполнитель)"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    versions = order_service.get_plan_versions(db, order_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Находим оригинальную версию
    original_plan = None
    if original_version:
        original_plan = next((v for v in versions if v.version_type.upper() == original_version.upper()), None)
    else:
        original_plan = next((v for v in versions if v.version_type.upper() == "ORIGINAL"), None)
    
    # Находим измененную версию
    modified_plan = None
    if modified_version:
        modified_plan = next((v for v in versions if v.version_type.upper() == modified_version.upper()), None)
    else:
        modified_plan = next((v for v in versions if v.version_type.upper() in ["MODIFIED", "EXECUTOR_EDITED"]), None)
        if not modified_plan and versions:
            modified_plan = versions[-1]  # Последняя версия
    
    original_response = None
    modified_response = None
    
    if original_plan:
        created_by_name = None
        if original_plan.created_by_id:
            from app.services import user_service
            creator = user_service.get_user_by_id(db, original_plan.created_by_id)
            if creator:
                created_by_name = creator.full_name
        original_response = Plan2DResponse(
            orderId=order_id,
            versionType=original_plan.version_type,
            versionId=original_plan.id,
            plan=original_plan.plan,
            comment=original_plan.comment,
            createdAt=original_plan.created_at,
            createdBy=created_by_name,
        )
    
    if modified_plan:
        created_by_name = None
        if modified_plan.created_by_id:
            from app.services import user_service
            creator = user_service.get_user_by_id(db, modified_plan.created_by_id)
            if creator:
                created_by_name = creator.full_name
        modified_response = Plan2DResponse(
            orderId=order_id,
            versionType=modified_plan.version_type,
            versionId=modified_plan.id,
            plan=modified_plan.plan,
            comment=modified_plan.comment,
            createdAt=modified_plan.created_at,
            createdBy=created_by_name,
        )
    
    # Вычисляем изменения
    changes = {}
    if original_plan and modified_plan:
        changes = _calculate_plan_diff_executor(original_plan.plan, modified_plan.plan)
    
    return PlanDiffResponse(
        original=original_response,
        modified=modified_response,
        changes=changes,
    )


def _calculate_plan_diff_executor(original_plan: dict, modified_plan: dict) -> dict:
    """Вычислить разницу между двумя планами для подсветки изменений (исполнитель)"""
    deleted = []
    added = []
    modified = []
    
    original_elements = {elem.get("id"): elem for elem in original_plan.get("elements", [])}
    modified_elements = {elem.get("id"): elem for elem in modified_plan.get("elements", [])}
    
    # Находим удаленные элементы
    for elem_id, elem in original_elements.items():
        if elem_id not in modified_elements:
            deleted.append(elem_id)
    
    # Находим добавленные элементы
    for elem_id, elem in modified_elements.items():
        if elem_id not in original_elements:
            added.append(elem_id)
    
    # Находим измененные элементы (изменилась геометрия или свойства)
    for elem_id in original_elements.keys() & modified_elements.keys():
        orig_elem = original_elements[elem_id]
        mod_elem = modified_elements[elem_id]
        # Сравниваем геометрию и основные свойства
        if orig_elem.get("geometry") != mod_elem.get("geometry") or \
           orig_elem.get("role") != mod_elem.get("role") or \
           orig_elem.get("zoneType") != mod_elem.get("zoneType"):
            modified.append(elem_id)
    
    return {
        "deleted": deleted,  # Красный
        "added": added,     # Зеленый
        "modified": modified,  # Желтый
    }


@router.get("/orders/{order_id}/plan/export", response_model=PlanExportResponse, summary="Экспорт плана в JSON (исполнитель)")
def export_plan_executor(
    order_id: uuid.UUID,
    version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlanExportResponse:
    """Экспортировать план в JSON формате (исполнитель)"""
    _ensure_executor(current_user)
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    versions = order_service.get_plan_versions(db, order_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Выбираем версию
    plan_version = None
    if version:
        match = next((v for v in versions if v.version_type.upper() == version.upper()), None)
        if match:
            plan_version = match
        else:
            raise HTTPException(status_code=404, detail=f"Plan version {version} not found")
    else:
        plan_version = versions[-1]  # Последняя версия
    
    # Формируем метаданные
    metadata = {
        "versionType": plan_version.version_type,
        "versionId": str(plan_version.id),
        "comment": plan_version.comment,
        "createdAt": plan_version.created_at.isoformat() if plan_version.created_at else None,
    }
    
    if plan_version.created_by_id:
        from app.services import user_service
        creator = user_service.get_user_by_id(db, plan_version.created_by_id)
        if creator:
            metadata["createdBy"] = creator.full_name
            metadata["createdByEmail"] = creator.email
    
    from datetime import datetime
    return PlanExportResponse(
        orderId=order_id,
        exportedAt=datetime.utcnow(),
        plan=plan_version.plan,
        metadata=metadata,
    )


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
