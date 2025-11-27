from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.schemas.auth import AuthTokenResponse, CurrentUserResponse, LoginRequest
from app.schemas.user import RegisterClientRequest
from app.services import user_service


def login(db: Session, data: LoginRequest) -> AuthTokenResponse:
    user = user_service.verify_user_credentials(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    token = create_access_token(str(user.id))
    return AuthTokenResponse(accessToken=token, tokenType="Bearer")


def get_me(user) -> CurrentUserResponse:
    return CurrentUserResponse(
        user=user,
        isClient=user.client_profile is not None,
        isExecutor=user.executor_profile is not None,
        isAdmin=user.is_admin,
    )


def register_client(db: Session, data: RegisterClientRequest):
    return user_service.create_client(db, data)
