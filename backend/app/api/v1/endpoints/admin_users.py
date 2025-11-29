import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.schemas.user import (
    ExecutorCreateRequest,
    ExecutorDetails,
    ExecutorAnalytics,
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


@router.get("/executors", response_model=list[ExecutorDetails], summary="Список исполнителей")
def list_executors(
    departmentCode: str | None = None,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[ExecutorDetails]:
    users = executor_service.list_executors_by_department(db, departmentCode)
    results: list[ExecutorDetails] = []
    for user in users:
        profile = user.executor_profile
        results.append(
            ExecutorDetails(
                user=user,
                executorProfile={
                    "departmentCode": profile.department_code if profile else None,
                    "experienceYears": profile.experience_years if profile else None,
                },
            )
        )
    return results


@router.get("/users", response_model=list[User], summary="Список пользователей")
def list_users(
    role: str | None = Query(default=None, description="Фильтр по роли: client, executor, admin"),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[User]:
    """Получить список пользователей с фильтром по роли"""
    users = user_service.list_users(db, role=role)
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


@router.get("/executors/analytics", response_model=list[ExecutorAnalytics], summary="Аналитика загрузки исполнителей")
def list_executors_analytics(
    department_code: str | None = Query(default=None, description="Фильтр по отделу"),
    search: str | None = Query(default=None, description="Поиск по ФИО или email"),
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[ExecutorAnalytics]:
    """Получить список исполнителей с аналитикой загрузки"""
    # Нормализуем параметры (убираем пробелы, None если пусто)
    dept_code = None
    if department_code:
        dept_code = department_code.strip()
        if not dept_code:  # Если после strip пустая строка
            dept_code = None
    
    search_term = None
    if search:
        search_term = search.strip()
        if not search_term:  # Если после strip пустая строка
            search_term = None
    
    analytics = executor_service.list_executors_with_analytics(db, dept_code, search_term)
    return analytics


@router.get("/executors/{executor_id}/analytics", response_model=ExecutorAnalytics, summary="Аналитика по конкретному исполнителю")
def get_executor_analytics(
    executor_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> ExecutorAnalytics:
    """Получить аналитику по конкретному исполнителю"""
    analytics = executor_service.get_executor_analytics(db, executor_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Executor not found or has no profile")
    return analytics


@router.get("/users/{user_id}/orders", response_model=list[dict], summary="История заказов пользователя")
def get_user_orders(
    user_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
) -> list[dict]:
    """Получить историю заказов пользователя (как клиента и как исполнителя)"""
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from app.services import order_service
    orders = order_service.get_user_orders(db, user_id)
    
    # Формируем упрощенный список заказов для админки
    result = []
    for order in orders:
        role = "client" if order.client_id == user_id else "executor"
        result.append({
            "id": str(order.id),
            "title": order.title,
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "role": role,
            "createdAt": order.created_at.isoformat() if order.created_at else None,
            "totalPrice": order.total_price,
            "address": order.address,
        })
    return result
