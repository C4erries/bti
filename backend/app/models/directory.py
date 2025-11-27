from sqlalchemy import Boolean, Float, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Department(Base):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    executors: Mapped[list["ExecutorProfile"]] = relationship(
        "ExecutorProfile", back_populates="department"
    )
    services: Mapped[list["Service"]] = relationship(
        "Service", back_populates="department"
    )


class Service(Base):
    __tablename__ = "services"

    code: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    department_code: Mapped[str | None] = mapped_column(String(50), ForeignKey("departments.code"))
    base_price: Mapped[float | None] = mapped_column(Float)
    base_duration_days: Mapped[int | None] = mapped_column(Integer)
    required_docs: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    department: Mapped["Department"] = relationship("Department", back_populates="services")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="service")


class District(Base):
    __tablename__ = "districts"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_coef: Mapped[float | None] = mapped_column(Float, default=1.0)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="district")


class HouseType(Base):
    __tablename__ = "house_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_coef: Mapped[float | None] = mapped_column(Float, default=1.0)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="house_type")
