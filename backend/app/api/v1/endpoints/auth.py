from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas.auth import AuthTokenResponse, CurrentUserResponse, LoginRequest
from app.schemas.user import RegisterClientRequest, User
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register/client",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация клиента",
    tags=["Auth"],
)
def register_client(data: RegisterClientRequest, db: Session = Depends(get_db_session)) -> User:
    try:
        user = auth_service.register_client(db, data)
        return User.model_validate(user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as e:
        # Логируем неожиданные ошибки для отладки
        import traceback
        print(f"Register error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) from e


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    summary="Логин",
    tags=["Auth"],
)
def login(data: LoginRequest, db: Session = Depends(get_db_session)) -> AuthTokenResponse:
    try:
        return auth_service.login(db, data)
    except HTTPException:
        raise
    except Exception as e:
        # Логируем неожиданные ошибки для отладки
        import traceback
        print(f"Login error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) from e


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Текущий пользователь",
    tags=["Auth"],
)
def read_me(current_user=Depends(get_current_user)) -> CurrentUserResponse:
    return auth_service.get_me(current_user)
