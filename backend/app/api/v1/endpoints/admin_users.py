import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.schemas.user import (
    ExecutorCreateRequest,
    ExecutorDetails,
    User,
    UserUpdateAdmin,
)
from app.services import executor_service, user_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/executors", response_model=ExecutorDetails, summary="Создать исполнителя")
def create_executor(
    data: ExecutorCreateRequest,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> ExecutorDetails:
    user = executor_service.create_executor(db, data)
    executor_profile = user.executor_profile
    return ExecutorDetails(user=user, executorProfile={"departmentCode": executor_profile.department_code if executor_profile else None, "experienceYears": executor_profile.experience_years if executor_profile else None})


@router.get("/users", response_model=list[User], summary="Список пользователей")
def list_users(
    db: Session = Depends(get_db_session), admin=Depends(get_current_admin)
) -> list[User]:
    users = user_service.list_users(db)
    return [User.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=User)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> User:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User.model_validate(user)


@router.patch("/users/{user_id}", response_model=User)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdateAdmin,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> User:
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_service.update_user_admin(db, user, data)
    return User.model_validate(user)
