from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, MeResponse, Token
from app.schemas.user import UserCreate
from app.services import user_service


def login(db: Session, data: LoginRequest) -> Token:
    user = user_service.verify_user_credentials(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    token = create_access_token(str(user.id))
    return Token(access_token=token, token_type="bearer")


def get_me(user) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_admin=user.is_admin,
        is_client=user.client_profile is not None,
        is_executor=user.executor_profile is not None,
        created_at=user.created_at,
        executor_department=(
            user.executor_profile.department_code if user.executor_profile else None
        ),
    )


def register_client(db: Session, data: UserCreate) -> Token:
    user = user_service.create_client(db, data)
    token = create_access_token(str(user.id))
    return Token(access_token=token, token_type="bearer")
