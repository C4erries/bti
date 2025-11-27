import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.schemas.user import ExecutorCreateRequest, UserDetail, UserUpdateAdmin
from app.services import executor_service, user_service

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.post("/executors", response_model=UserDetail, summary="Создать исполнителя")
def create_executor(
    data: ExecutorCreateRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> UserDetail:
    user = executor_service.create_executor(db, data)
    return UserDetail.model_validate(user)


@router.get("/users", response_model=list[UserDetail], summary="Список пользователей")
def list_users(
    db: Session = Depends(get_db_session), admin=Depends(get_current_admin)
) -> list[UserDetail]:
    users = user_service.list_users(db)
    return [UserDetail.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserDetail)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> UserDetail:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserDetail.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserDetail)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdateAdmin,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> UserDetail:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_service.update_user_admin(db, user, data)
    return UserDetail.model_validate(user)
