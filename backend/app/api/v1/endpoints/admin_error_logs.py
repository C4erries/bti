"""API endpoints для журнала ошибок"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.models.error_log import ErrorLog, ErrorType, ErrorSeverity, ErrorStatus
from app.schemas.error_log import ErrorLogCreate, ErrorLogRead, ErrorLogUpdate
from app.services import error_log_service, user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/error-logs", response_model=list[ErrorLogRead], summary="Список ошибок")
def list_error_logs(
    errorType: ErrorType | None = Query(default=None, alias="errorType", description="Фильтр по типу ошибки"),
    status: ErrorStatus | None = Query(default=None, description="Фильтр по статусу"),
    severity: ErrorSeverity | None = Query(default=None, description="Фильтр по критичности"),
    assignedToId: uuid.UUID | None = Query(default=None, alias="assignedToId", description="Фильтр по ответственному"),
    search: str | None = Query(default=None, description="Поиск по сообщению"),
    limit: int = Query(default=100, le=500, description="Лимит записей"),
    offset: int = Query(default=0, ge=0, description="Смещение"),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[ErrorLogRead]:
    """Получить список записей об ошибках с фильтрами"""
    logs, total = error_log_service.list_error_logs(
        db,
        error_type=errorType,
        status=status,
        severity=severity,
        assigned_to_id=assignedToId,
        search=search,
        limit=limit,
        offset=offset,
    )
    
    result = []
    for log in logs:
        assigned_to_name = None
        if log.assigned_to_id:
            user = user_service.get_user_by_id(db, log.assigned_to_id)
            if user:
                assigned_to_name = user.full_name
        
        log_data = ErrorLogRead.model_validate(log)
        log_data.assigned_to_name = assigned_to_name
        result.append(log_data)
    
    return result


@router.get("/error-logs/{log_id}", response_model=ErrorLogRead, summary="Детали ошибки")
def get_error_log(
    log_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> ErrorLogRead:
    """Получить запись об ошибке по ID"""
    log = error_log_service.get_error_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Error log not found")
    
    assigned_to_name = None
    if log.assigned_to_id:
        user = user_service.get_user_by_id(db, log.assigned_to_id)
        if user:
            assigned_to_name = user.full_name
    
    log_data = ErrorLogRead.model_validate(log)
    log_data.assigned_to_name = assigned_to_name
    return log_data


@router.post("/error-logs", response_model=ErrorLogRead, status_code=201, summary="Создать запись об ошибке")
def create_error_log(
    data: ErrorLogCreate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> ErrorLogRead:
    """Создать новую запись об ошибке (для внутреннего использования)"""
    log = error_log_service.create_error_log(db, data)
    return ErrorLogRead.model_validate(log)


@router.patch("/error-logs/{log_id}", response_model=ErrorLogRead, summary="Обновить запись об ошибке")
def update_error_log(
    log_id: uuid.UUID,
    data: ErrorLogUpdate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> ErrorLogRead:
    """Обновить запись об ошибке (статус, ответственный)"""
    log = error_log_service.get_error_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Error log not found")
    
    log = error_log_service.update_error_log(db, log, data)
    
    assigned_to_name = None
    if log.assigned_to_id:
        user = user_service.get_user_by_id(db, log.assigned_to_id)
        if user:
            assigned_to_name = user.full_name
    
    log_data = ErrorLogRead.model_validate(log)
    log_data.assigned_to_name = assigned_to_name
    return log_data

