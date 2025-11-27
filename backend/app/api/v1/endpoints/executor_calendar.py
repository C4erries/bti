from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas.orders import ExecutorCalendarEvent
from app.services import order_service

router = APIRouter(prefix="/executor", tags=["Executor"])


@router.get("/calendar", response_model=list[ExecutorCalendarEvent])
def get_calendar(
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[ExecutorCalendarEvent]:
    if not current_user.executor_profile:
        raise HTTPException(status_code=403, detail="Executor profile required")
    events = order_service.get_executor_calendar(db, current_user.id)
    return [ExecutorCalendarEvent.model_validate(e) for e in events]
