import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas.orders import (
    CreateOrderRequest,
    Order,
    UpdateOrderRequest,
    OrderFile,
    OrderPlanVersion,
    OrderStatusHistoryItem,
    SavePlanChangesRequest,
    ParsePlanResultRequest,
    AiAnalysis,
)
from app.schemas.plan_responses import (
    Plan2DResponse,
    PlanBeforeAfterResponse,
    PlanDiffResponse,
    PlanExportResponse,
)
from app.models.order import OrderFile as OrderFileModel
from app.core.config import settings
from app.services import order_service

class HTTPValidationError(BaseModel):
    detail: list[dict] | None = None

router = APIRouter(prefix="/client", tags=["Client"])


def _ensure_ownership(order, user_id: uuid.UUID):
    if order.client_id != user_id:
        raise HTTPException(status_code=403, detail="Not your order")


@router.get("/orders", response_model=list[Order])
def list_client_orders(
    db: Session = Depends(get_db_session), current_user=Depends(get_current_user)
) -> list[Order]:
    orders = order_service.get_client_orders(db, current_user.id)
    return [Order.model_validate(o) for o in orders]


@router.post(
    "/orders",
    response_model=Order,
    status_code=201,
    responses={422: {"model": HTTPValidationError}},
)
def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> Order:
    order = order_service.create_order(db, current_user, payload)
    return Order.model_validate(order)




@router.get("/orders/{order_id}", response_model=Order)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> Order:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    return Order.model_validate(order)


@router.patch("/orders/{order_id}", response_model=Order)
def update_order(
    order_id: uuid.UUID,
    payload: UpdateOrderRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> Order:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    order = order_service.update_order_by_client(db, order, payload)
    return Order.model_validate(order)


@router.post("/orders/{order_id}/files", response_model=OrderFile, status_code=201)
def upload_file(
    order_id: uuid.UUID,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderFile:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    file = order_service.add_file(db, order, upload, uploaded_by=current_user)
    return OrderFile.model_validate(file)


@router.get("/orders/{order_id}/files", response_model=list[OrderFile])
def get_files(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderFile]:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    files = order_service.get_order_files(db, order_id)
    return [OrderFile.model_validate(f) for f in files]


@router.get("/orders/{order_id}/plan", response_model=OrderPlanVersion)
def get_plan_versions(
    order_id: uuid.UUID,
    version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderPlanVersion:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    versions = order_service.get_plan_versions(db, order_id)
    if version:
        match = next((v for v in versions if v.version_type.lower() == version.lower()), None)
        if match:
            return OrderPlanVersion.model_validate(match)
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    return OrderPlanVersion.model_validate(versions[-1])


@router.get("/orders/{order_id}/plan/2d", response_model=Plan2DResponse, summary="Получить 2D план с полной геометрией")
def get_plan_2d(
    order_id: uuid.UUID,
    version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> Plan2DResponse:
    """Получить 2D план с полной геометрией (meta, elements, objects3d) для визуализации"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    
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


@router.get("/orders/{order_id}/plan/before-after", response_model=PlanBeforeAfterResponse, summary="Получить план в режиме до/после")
def get_plan_before_after(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlanBeforeAfterResponse:
    """Получить две версии плана (ORIGINAL и MODIFIED) для режима до/после"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    
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


@router.get("/orders/{order_id}/plan/diff", response_model=PlanDiffResponse, summary="Получить разницу между версиями плана")
def get_plan_diff(
    order_id: uuid.UUID,
    original_version: str | None = None,
    modified_version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlanDiffResponse:
    """Получить разницу между версиями плана с подсветкой изменений (красный/зеленый/желтый)"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    
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
        changes = _calculate_plan_diff(original_plan.plan, modified_plan.plan)
    
    return PlanDiffResponse(
        original=original_response,
        modified=modified_response,
        changes=changes,
    )


def _calculate_plan_diff(original_plan: dict, modified_plan: dict) -> dict:
    """Вычислить разницу между двумя планами для подсветки изменений"""
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


@router.get("/orders/{order_id}/plan/export", response_model=PlanExportResponse, summary="Экспорт плана в JSON")
def export_plan(
    order_id: uuid.UUID,
    version: str | None = None,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> PlanExportResponse:
    """Экспортировать план в JSON формате для сохранения/передачи"""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    
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


@router.post("/orders/{order_id}/plan/parse-result", response_model=OrderPlanVersion, summary="Принять результат парсинга плана от нейронки")
def parse_plan_result(
    order_id: uuid.UUID,
    payload: ParsePlanResultRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderPlanVersion:
    """
    Принять результат парсинга плана от нейронки.
    Автоматически создает версию плана ORIGINAL и связывает с загруженным файлом.
    """
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    
    # Проверяем, что файл существует и принадлежит этому заказу
    from app.models.order import OrderFile as OrderFileModel
    file_obj = db.get(OrderFileModel, payload.file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    if file_obj.order_id != order_id:
        raise HTTPException(status_code=400, detail="File does not belong to this order")
    
    # Формируем комментарий с информацией о парсинге
    comment_parts = ["Результат автоматического парсинга плана"]
    if payload.confidence is not None:
        comment_parts.append(f"Уверенность: {payload.confidence:.0%}")
    if payload.errors:
        comment_parts.append(f"Предупреждения: {', '.join(payload.errors)}")
    if payload.processing_time_ms is not None:
        comment_parts.append(f"Время обработки: {payload.processing_time_ms}мс")
    
    comment = " | ".join(comment_parts)
    
    # Создаем версию плана ORIGINAL
    from app.schemas.orders import SavePlanChangesRequest
    plan_request = SavePlanChangesRequest(
        versionType="ORIGINAL",
        plan=payload.plan,
        comment=comment,
    )
    
    # Создаем версию плана (created_by может быть None, если это автоматический парсинг)
    version = order_service.add_plan_version(db, order, plan_request, created_by=current_user)
    
    return OrderPlanVersion.model_validate(version)


@router.post("/orders/{order_id}/plan/changes", response_model=OrderPlanVersion)
def add_plan_change(
    order_id: uuid.UUID,
    payload: SavePlanChangesRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> OrderPlanVersion:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    version = order_service.add_plan_version(db, order, payload, created_by=current_user)
    return OrderPlanVersion.model_validate(version)


@router.get("/orders/{order_id}/status-history", response_model=list[OrderStatusHistoryItem])
def get_status_history(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[OrderStatusHistoryItem]:
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    history = order_service.get_status_history(db, order_id)
    return [OrderStatusHistoryItem.model_validate(h) for h in history]




@router.post("/orders/{order_id}/ai/analyze", response_model=AiAnalysis)
def trigger_ai_analyze(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    analysis = AiAnalysis(
        id=uuid.uuid4(),
        orderId=order_id,
        decisionStatus="UNKNOWN",
        summary=None,
        risks=[],
        legalWarnings=None,
        financialWarnings=None,
        rawResponse=None,
    )
    return analysis


@router.get("/orders/{order_id}/files/{file_id}")
def download_file(
    order_id: uuid.UUID,
    file_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    file = db.get(OrderFileModel, file_id)
    if not file or file.order_id != order_id:
        files = order_service.get_order_files(db, order_id)
        file = next((f for f in files if f.id == file_id), None)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    # map stored path (/static/orders/..) to filesystem
    relative = file.path.lstrip("/")
    static_root = Path(settings.static_root)
    fs_path = static_root / relative.split("/", 1)[1] if "/" in relative else static_root / relative
    if not fs_path.exists():
        raise HTTPException(status_code=404, detail="File content not found")
    return FileResponse(path=fs_path, filename=file.filename)


@router.get("/orders/{order_id}/ai/analysis", response_model=AiAnalysis)
def get_ai_analysis(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    analysis = AiAnalysis(
        id=uuid.uuid4(),
        orderId=order_id,
        decisionStatus="UNKNOWN",
        summary=None,
        risks=[],
        legalWarnings=None,
        financialWarnings=None,
        rawResponse=None,
    )
    return analysis
