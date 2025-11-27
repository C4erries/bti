from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import ClientProfile, ExecutorProfile, User
from app.schemas.user import ExecutorCreateRequest, UserCreate, UserUpdateAdmin


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id) -> User | None:
    return db.get(User, user_id)


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)))


def create_user(db: Session, data: UserCreate) -> User:
    existing = get_user_by_email(db, data.email)
    if existing:
        raise ValueError("User with this email already exists")
    user = User(
        email=data.email,
        full_name=data.full_name,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
        is_admin=data.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_client(db: Session, data: UserCreate) -> User:
    user = create_user(db, data)
    db.add(ClientProfile(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def create_executor(db: Session, data: ExecutorCreateRequest) -> User:
    user = create_user(
        db,
        UserCreate(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            phone=data.phone,
            is_admin=data.is_admin if hasattr(data, "is_admin") and data.is_admin is not None else False,
        ),
    )
    profile = ExecutorProfile(
        user_id=user.id,
        department_code=data.department_code,
        experience_years=data.experience_years,
        specialization=getattr(data, "specialization", None),
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def update_user_admin(db: Session, user: User, data: UserUpdateAdmin) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.is_admin is not None:
        user.is_admin = data.is_admin
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_client_profile(db: Session, user: User) -> ClientProfile:
    if user.client_profile:
        return user.client_profile
    profile = ClientProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def verify_user_credentials(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_executor_profiles_by_department(db: Session, department_code: str | None = None) -> Iterable[ExecutorProfile]:
    query = select(ExecutorProfile)
    if department_code:
        query = query.where(ExecutorProfile.department_code == department_code)
    return db.scalars(query).all()
