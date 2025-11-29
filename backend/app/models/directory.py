from sqlalchemy import Float, String, Text
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
