from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.schemas.auth import LoginRequest, MeResponse, Token
from app.schemas.user import UserCreate
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=Token, summary="Вход по email и паролю")
def login(data: LoginRequest, db: Session = Depends(get_db_session)) -> Token:
    return auth_service.login(db, data)


@router.post("/register", response_model=Token, summary="Регистрация клиента")
def register(data: UserCreate, db: Session = Depends(get_db_session)) -> Token:
    try:
        return auth_service.register_client(db, data)
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/me", response_model=MeResponse, summary="Текущий пользователь")
def read_me(current_user=Depends(get_current_user)) -> MeResponse:
    return auth_service.get_me(current_user)
