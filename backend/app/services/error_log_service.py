"""Сервис для работы с журналом ошибок"""
from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.models.error_log import ErrorLog, ErrorType, ErrorSeverity, ErrorStatus
from app.schemas.error_log import ErrorLogCreate, ErrorLogUpdate


def list_error_logs(
    db: Session,
    error_type: ErrorType | None = None,
    status: ErrorStatus | None = None,
    severity: ErrorSeverity | None = None,
    assigned_to_id: uuid.UUID | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ErrorLog], int]:
    """Получить список записей об ошибках с фильтрами"""
    query = select(ErrorLog)
    count_query = select(func.count()).select_from(ErrorLog)
    
    conditions = []
    
    if error_type:
        conditions.append(ErrorLog.error_type == error_type)
    
    if status:
        conditions.append(ErrorLog.status == status)
    
    if severity:
        conditions.append(ErrorLog.severity == severity)
    
    if assigned_to_id:
        conditions.append(ErrorLog.assigned_to_id == assigned_to_id)
    
    if search:
        search_pattern = f"%{search}%"
        conditions.append(ErrorLog.message.ilike(search_pattern))
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Общее количество
    total = db.scalar(count_query) or 0
    
    # Список с пагинацией
    query = query.order_by(ErrorLog.created_at.desc()).limit(limit).offset(offset)
    
    logs = list(db.scalars(query).all())
    
    return logs, total


def get_error_log(db: Session, log_id: uuid.UUID) -> ErrorLog | None:
    """Получить запись об ошибке по ID"""
    return db.get(ErrorLog, log_id)


def create_error_log(db: Session, data: ErrorLogCreate) -> ErrorLog:
    """Создать новую запись об ошибке"""
    error_log = ErrorLog(
        error_type=data.error_type,
        input_data=data.input_data,
        message=data.message,
        severity=data.severity,
        status=data.status,
        assigned_to_id=data.assigned_to_id,
    )
    db.add(error_log)
    db.commit()
    db.refresh(error_log)
    return error_log


def update_error_log(db: Session, error_log: ErrorLog, data: ErrorLogUpdate) -> ErrorLog:
    """Обновить запись об ошибке"""
    if data.status is not None:
        error_log.status = data.status
        if data.status == ErrorStatus.RESOLVED and error_log.resolved_at is None:
            error_log.resolved_at = datetime.utcnow()
        elif data.status != ErrorStatus.RESOLVED:
            error_log.resolved_at = None
    
    if data.assigned_to_id is not None:
        error_log.assigned_to_id = data.assigned_to_id
    
    if data.message is not None:
        error_log.message = data.message
    
    db.add(error_log)
    db.commit()
    db.refresh(error_log)
    return error_log


def log_error(
    db: Session,
    error_type: ErrorType,
    message: str,
    input_data: dict | None = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
) -> ErrorLog:
    """Вспомогательная функция для логирования ошибки (для внутреннего использования)"""
    error_log = ErrorLog(
        error_type=error_type,
        input_data=input_data,
        message=message,
        severity=severity,
        status=ErrorStatus.NEW,
    )
    db.add(error_log)
    db.commit()
    db.refresh(error_log)
    return error_log

