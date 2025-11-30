import math
import uuid
from copy import deepcopy
from datetime import datetime
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
    AiRisk,
    RecognizePlanRequest,
)
from app.schemas.plan_responses import (
    Plan2DResponse,
    PlanBeforeAfterResponse,
    PlanDiffResponse,
    PlanExportResponse,
)
from app.models.order import OrderFile as OrderFileModel
from app.core.config import settings
from app.services import order_service, plan_recognition_service, ai_rule_service
from app.services.gemini_client import generate_json
from app.services.plan_description import summarize_plan

class HTTPValidationError(BaseModel):
    detail: list[dict] | None = None

router = APIRouter(prefix="/client", tags=["Client"])


def _ensure_ownership(order, user_id: uuid.UUID):
    if order.client_id != user_id:
        raise HTTPException(status_code=403, detail="Not your order")


def _split_wall_segments(plan: dict) -> dict:
    """Split walls with openings into separate wall elements without openings."""
    if not plan:
        return plan
    meta = plan.get("meta", {}) or {}
    scale = meta.get("scale") or {}
    px_per_meter = scale.get("px_per_meter") or scale.get("pxPerMeter") or 1
    try:
        px_per_meter = float(px_per_meter)
        if px_per_meter <= 0:
            px_per_meter = 1
    except Exception:
        px_per_meter = 1

    elements = []
    for elem in plan.get("elements", []):
        if elem.get("type") != "wall":
            elements.append(elem)
            continue
        geom = elem.get("geometry") or {}
        openings = geom.get("openings") or []
        points = geom.get("points") or []
        if geom.get("kind") != "segment" or len(points) != 4 or not openings:
            elements.append(elem)
            continue

        x1, y1, x2, y2 = points
        dx = x2 - x1
        dy = y2 - y1
        length_px = math.hypot(dx, dy)
        if length_px == 0:
            elements.append(elem)
            continue
        length_m = length_px / px_per_meter if px_per_meter else length_px

        def point_at(offset_m: float) -> tuple[float, float]:
            offset_px = offset_m * px_per_meter
            ratio = offset_px / length_px
            return x1 + dx * ratio, y1 + dy * ratio

        openings_sorted = sorted(openings, key=lambda o: o.get("from_m", 0))
        segments: list[tuple[float, float]] = []
        cursor = 0.0
        for op in openings_sorted:
            start = max(0.0, float(op.get("from_m", 0)))
            end = max(start, float(op.get("to_m", start)))
            start = min(start, length_m)
            end = min(end, length_m)
            if start > cursor:
                segments.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < length_m:
            segments.append((cursor, length_m))

        if not segments:
            elements.append(elem)
            continue

        for idx, (seg_start, seg_end) in enumerate(segments):
            if seg_end - seg_start <= 0:
                continue
            sx, sy = point_at(seg_start)
            ex, ey = point_at(seg_end)
            new_elem = deepcopy(elem)
            new_elem["id"] = f"{elem.get('id')}_seg{idx+1}"
            new_elem_geom = deepcopy(geom)
            new_elem_geom["points"] = [sx, sy, ex, ey]
            new_elem_geom["openings"] = None
            new_elem["geometry"] = new_elem_geom
            elements.append(new_elem)

    plan_copy = deepcopy(plan)
    plan_copy["elements"] = elements
    return plan_copy


def _apply_split_to_plan_version(plan_version):
    if not plan_version or not getattr(plan_version, "plan", None):
        return plan_version
    plan_version.plan = _split_wall_segments(plan_version.plan)
    return plan_version


def _format_rules_text(rules: list) -> str:
    if not rules:
        return "Правила для анализа не заданы."
    lines = []
    for rule in rules[:5]:
        title = getattr(rule, "name", None) or "Правило"
        description = getattr(rule, "description", None) or getattr(rule, "trigger_condition", "") or ""
        risk_type = getattr(rule, "risk_type", None)
        severity = getattr(rule, "severity", None)
        parts = [f"- {title}: {description}"]
        extra = []
        if risk_type:
            extra.append(f"тип риска {getattr(risk_type, 'value', risk_type)}")
        if severity:
            extra.append(f"серьезность {severity}")
        if extra:
            parts.append(f"({', '.join(extra)})")
        lines.append(" ".join(parts).strip())
    return "\n".join(lines)


def _severity_from_label(label: str | None) -> int | None:
    if not label:
        return None
    mapping = {"low": 1, "medium": 2, "high": 4, "critical": 5}
    return mapping.get(label.lower())


def _map_ai_risk(risk_dict: dict) -> AiRisk:
    severity = risk_dict.get("severity")
    if severity is None:
        severity = _severity_from_label(risk_dict.get("severity_str"))
    risk_type = risk_dict.get("type") or "TECHNICAL"
    description = risk_dict.get("description") or "Risk details are not available"
    return AiRisk(
        type=risk_type,
        description=description,
        severity=severity,
        zone=risk_dict.get("zone"),
    )


def _derive_decision_status(risks: list[AiRisk]) -> str:
    if any(r.severity and r.severity >= 4 for r in risks):
        return "FORBIDDEN"
    if any(r.severity and r.severity >= 3 for r in risks):
        return "NEEDS_APPROVAL"
    if risks:
        return "ALLOWED_WITH_WARNINGS"
    return "ALLOWED"


def _collect_order_context(order) -> dict:
    status_value = order.status.value if hasattr(order.status, "value") else str(order.status)
    context = {
        "order_id": str(order.id),
        "order_title": order.title,
        "order_status": status_value,
    }
    if order.district_code:
        context["district_code"] = order.district_code
    if order.house_type_code:
        context["house_type_code"] = order.house_type_code
    if order.address:
        context["address"] = order.address
    if getattr(order, "area", None):
        context["area"] = order.area
    return context


def _get_latest_plan_data(db: Session, order_id: uuid.UUID) -> dict | None:
    versions = order_service.get_plan_versions(db, order_id)
    if not versions:
        return None
    latest = versions[-1]
    latest = _apply_split_to_plan_version(latest)
    return latest.plan


async def _build_ai_analysis(db: Session, order, persist: bool = False) -> AiAnalysis:
    plan_data = _get_latest_plan_data(db, order.id)
    if not plan_data:
        summary = order.ai_decision_summary or "Plan data not available for analysis"
        decision_status = order.ai_decision_status or "UNKNOWN"
        analysis = AiAnalysis(
            id=uuid.uuid4(),
            orderId=order.id,
            decisionStatus=decision_status,
            summary=summary,
            risks=None,
            legalWarnings=None,
            financialWarnings=None,
            rawResponse=None,
        )
        if persist:
            order.ai_decision_status = decision_status
            order.ai_decision_summary = summary
            db.add(order)
            db.commit()
            db.refresh(order)
        return analysis

    rules = ai_rule_service.list_rules(db, is_enabled=True)
    rules_text = _format_rules_text(rules)
    order_context = _collect_order_context(order)
    plan_description = summarize_plan(plan_data)

    system_prompt = (
        "Ты эксперт по перепланировкам и БТИ. "
        "Анализируй план квартиры, оценивай риски и формируй структурированный вывод."
    )
    prompt = (
        f"Данные заказа:\n"
        f"ID: {order_context.get('order_id')}\n"
        f"Статус: {order_context.get('order_status')}\n"
        f"Тип дома: {order_context.get('house_type_code', 'не указан')}\n"
        f"Округ: {order_context.get('district_code', 'не указан')}\n"
        f"Адрес: {order_context.get('address', 'не указан')}\n\n"
        f"Описание плана:\n{plan_description}\n\n"
        f"Правила и ограничения:\n{rules_text}\n\n"
        "Сформируй краткое резюме и список рисков по категориям "
        "(TECHNICAL, LEGAL, FINANCIAL, OPERATIONAL). "
        "Ответ верни строго в JSON с полями: summary (str), risks (list of objects: "
        "type, description, severity(1-5), zone(optional))."
    )

    result = await generate_json(
        system=system_prompt,
        prompt=prompt,
        temperature=settings.analysis_temperature,
    )

    risks_dicts = result.get("risks") if isinstance(result, dict) else []
    summary = result.get("summary") if isinstance(result, dict) else None

    ai_risks = [_map_ai_risk(r) for r in risks_dicts] if risks_dicts else []
    decision_status = result.get("decisionStatus") if isinstance(result, dict) else None
    derived_status = _derive_decision_status(ai_risks)
    if derived_status:
        decision_status = derived_status
    if not decision_status:
        decision_status = order.ai_decision_status or "UNKNOWN"
    if not summary:
        summary = "Анализ плана не дал результатов."

    analysis = AiAnalysis(
        id=uuid.uuid4(),
        orderId=order.id,
        decisionStatus=decision_status,
        summary=summary,
        risks=ai_risks or None,
        legalWarnings=None,
        financialWarnings=None,
        rawResponse=result if isinstance(result, dict) else None,
    )

    if persist:
        order.ai_decision_status = decision_status
        order.ai_decision_summary = summary
        db.add(order)
        db.commit()
        db.refresh(order)

    return analysis


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
            match = _apply_split_to_plan_version(match)
            return OrderPlanVersion.model_validate(match)
    if not versions:
        raise HTTPException(status_code=404, detail="Plan not found")
    latest = _apply_split_to_plan_version(versions[-1])
    return OrderPlanVersion.model_validate(latest)


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
    
    plan_version = _apply_split_to_plan_version(plan_version)

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
            v = _apply_split_to_plan_version(v)
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
            v = _apply_split_to_plan_version(v)
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
        original_plan = _apply_split_to_plan_version(original_plan)
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
        modified_plan = _apply_split_to_plan_version(modified_plan)
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
    plan_version = _apply_split_to_plan_version(plan_version)
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
    
    version = _apply_split_to_plan_version(version)
    version = _apply_split_to_plan_version(version)
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
    version = _apply_split_to_plan_version(version)
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
    
    try:
        history = order_service.get_status_history(db, order_id)
        result = []
        for h in history:
            try:
                history_item = OrderStatusHistoryItem.model_validate(h)
                # Если есть changed_by, добавляем информацию о пользователе
                if h.changed_by:
                    from app.schemas.user import User
                    history_item.changed_by = User.model_validate(h.changed_by).model_dump()
                result.append(history_item)
            except Exception as e:
                print(f"Error validating history item {h.id}: {e}")
                # Создаем упрощенную версию
                result.append(OrderStatusHistoryItem(
                    id=h.id,
                    orderId=h.order_id,
                    status=h.status.value if hasattr(h.status, 'value') else str(h.status),
                    changedByUserId=h.changed_by_id,
                    changedAt=h.created_at,
                    comment=h.comment
                ))
        return result
    except Exception as e:
        import traceback
        print(f"Error in get_status_history (client): {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving status history: {str(e)}")




@router.post("/orders/{order_id}/ai/analyze", response_model=AiAnalysis)
async def trigger_ai_analyze(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)

    analysis = await _build_ai_analysis(db, order, persist=True)
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
async def get_ai_analysis(
    order_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)
    analysis = await _build_ai_analysis(db, order, persist=False)
    return analysis


@router.post(
    "/orders/{order_id}/plan/recognize",
    response_model=OrderPlanVersion,
    summary="Распознать план по загруженному файлу",
)
def recognize_plan(
    order_id: uuid.UUID,
    payload: RecognizePlanRequest,
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_ownership(order, current_user.id)

    file = db.get(OrderFileModel, payload.file_id)
    if not file or file.order_id != order_id:
        raise HTTPException(status_code=404, detail="File not found for this order")

    plan = plan_recognition_service.get_plan_by_filename(file.filename)
    if not plan:
        raise HTTPException(status_code=422, detail="No plan template found for this filename")

    existing_versions = order_service.get_plan_versions(db, order_id)
    has_original = any(v.version_type.upper() == "ORIGINAL" for v in existing_versions)
    version_type = "MODIFIED" if has_original else "ORIGINAL"
    comment = f"Распознан план по изображению {file.filename}"

    plan_request = SavePlanChangesRequest(versionType=version_type, plan=plan, comment=comment)
    version = order_service.add_plan_version(db, order, plan_request, created_by=current_user)
    return OrderPlanVersion.model_validate(version)
