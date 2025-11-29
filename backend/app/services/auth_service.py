from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.schemas.auth import AuthTokenResponse, CurrentUserResponse, LoginRequest
from app.schemas.user import RegisterClientRequest
from app.services import user_service


def login(db: Session, data: LoginRequest) -> AuthTokenResponse:
    """Логин пользователя с детальной обработкой ошибок"""
    try:
        # Проверяем, существует ли пользователь
        user = user_service.get_user_by_email(db, data.email)
        if not user:
            print(f"DEBUG LOGIN: User not found for email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid email or password"
            )
        
        print(f"DEBUG LOGIN: User found: {user.email}, is_blocked: {user.is_blocked}")
        
        # Проверяем блокировку
        if user.is_blocked:
            print(f"DEBUG LOGIN: User is blocked: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is blocked"
            )
        
        # Проверяем пароль
        from app.core.security import verify_password
        password_valid = verify_password(data.password, user.password_hash)
        print(f"DEBUG LOGIN: Password verification result: {password_valid}")
        
        if not password_valid:
            print(f"DEBUG LOGIN: Password verification failed for user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        print(f"DEBUG LOGIN: Login successful for user: {user.email}")
        token = create_access_token(str(user.id))
        return AuthTokenResponse(accessToken=token, tokenType="Bearer")
    except HTTPException:
        raise
    except Exception as e:
        # Логируем ошибки для отладки
        import traceback
        print(f"Login service error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        ) from e


def get_me(user) -> CurrentUserResponse:
    return CurrentUserResponse(
        user=user,
        isClient=user.client_profile is not None,
        isExecutor=user.executor_profile is not None,
        isAdmin=user.is_admin or user.is_superadmin,
        isSuperadmin=user.is_superadmin,
    )


def register_client(db: Session, data: RegisterClientRequest):
    return user_service.create_client(db, data)
