from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import AssignmentStatus, ExecutorAssignment
from app.models.user import ExecutorProfile, User
from app.schemas.user import ExecutorCreateRequest
from app.services import order_service, user_service


def create_executor(db: Session, data: ExecutorCreateRequest) -> User:
    return user_service.create_executor(db, data)


def list_executors(db: Session, department_code: str | None = None) -> list[ExecutorProfile]:
    query = select(ExecutorProfile)
    if department_code:
        query = query.where(ExecutorProfile.department_code == department_code)
    return list(db.scalars(query))


def get_executor_load(db: Session, executor_id) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ExecutorAssignment)
            .where(
                ExecutorAssignment.executor_id == executor_id,
                ExecutorAssignment.status != AssignmentStatus.DECLINED,
            )
        )
        or 0
    )


def get_calendar(db: Session, executor_id):
    return order_service.get_executor_calendar(db, executor_id)
