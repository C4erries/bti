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
    AiAnalysis,
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
    version = order_service.add_plan_version(db, order, payload)
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
