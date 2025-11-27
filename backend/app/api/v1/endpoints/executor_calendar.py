from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas.orders import CalendarEventRead
from app.services import order_service

router = APIRouter(prefix="/executor", tags=["executor-calendar"])


@router.get("/calendar", response_model=list[CalendarEventRead])
def get_calendar(
    db: Session = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[CalendarEventRead]:
    if not current_user.executor_profile:
        raise HTTPException(status_code=403, detail="Executor profile required")
    events = order_service.get_executor_calendar(db, current_user.id)
    return [CalendarEventRead.model_validate(e) for e in events]
