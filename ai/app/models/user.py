"""Pydantic-модели для профиля пользователя."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ChildInfo(BaseModel):
    """Информация о ребенке."""
    age: int = Field(..., ge=0, le=18, description="Возраст ребенка")


class UserProfile(BaseModel):
    """Упрощенная модель профиля пользователя для персонализации."""
    height: Optional[float] = Field(None, ge=0, description="Рост пользователя в см")
    age: Optional[int] = Field(None, ge=0, description="Возраст пользователя")
    marital_status: Optional[Literal["single", "married", "divorced", "widowed"]] = Field(
        None, description="Семейное положение"
    )
    hobbies: Optional[List[str]] = Field(None, description="Увлечения пользователя")
    profession: Optional[str] = Field(None, description="Профессия пользователя")
    children: Optional[List[ChildInfo]] = Field(None, description="Информация о детях (количество и возраст)")

