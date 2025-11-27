import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.types import GUID


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    client_profile: Mapped["ClientProfile"] = relationship(
        back_populates="user", uselist=False
    )
    executor_profile: Mapped["ExecutorProfile"] = relationship(
        back_populates="user", uselist=False
    )
    client_orders: Mapped[list["Order"]] = relationship(
        back_populates="client", foreign_keys="Order.client_id"
    )
    executor_assignments: Mapped[list["ExecutorAssignment"]] = relationship(
        back_populates="executor", foreign_keys="ExecutorAssignment.executor_id"
    )


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    organization_name: Mapped[str | None] = mapped_column(String(255))
    is_legal_entity: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(String(500))

    user: Mapped[User] = relationship(back_populates="client_profile")


class ExecutorProfile(Base):
    __tablename__ = "executor_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    department_code: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("departments.code")
    )
    experience_years: Mapped[int | None] = mapped_column(Integer)
    specialization: Mapped[str | None] = mapped_column(String(255))

    user: Mapped[User] = relationship(back_populates="executor_profile")
    department: Mapped["Department"] = relationship("Department", back_populates="executors")
