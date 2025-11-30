"""Pydantic-модели для описания структуры данных плана на основе OrderPlanVersion."""

from typing import List, Optional, Literal, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PlanScale(BaseModel):
    """Масштаб плана."""
    px_per_meter: float = Field(..., gt=0)


class PlanBackground(BaseModel):
    """Фон плана."""
    file_id: str
    opacity: float = Field(..., ge=0, le=1)


class PlanMeta(BaseModel):
    """Метаданные плана."""
    width: float = Field(..., ge=0)
    height: float = Field(..., ge=0)
    unit: Literal["px"] = "px"
    scale: Optional[PlanScale] = None
    background: Optional[PlanBackground] = None
    ceiling_height_m: Optional[float] = Field(None, ge=1.8, le=5)


class Opening(BaseModel):
    """Проём в стене (дверь/окно)."""
    id: str
    type: Literal["door", "window", "arch", "custom"]
    from_m: float = Field(..., ge=0)
    to_m: float = Field(..., ge=0)
    bottom_m: float = Field(..., ge=0)
    top_m: float = Field(..., ge=0)


class WallGeometry(BaseModel):
    """Геометрия стены."""
    kind: Literal["segment"] = "segment"
    points: List[float] = Field(..., min_length=4, max_length=4)  # [x1, y1, x2, y2]
    openings: Optional[List[Opening]] = None


class PolygonGeometry(BaseModel):
    """Геометрия многоугольника."""
    kind: Literal["polygon"] = "polygon"
    points: List[float] = Field(..., min_length=6)  # [x1, y1, x2, y2, ..., xn, yn]


class PointGeometry(BaseModel):
    """Геометрия точки."""
    kind: Literal["point"] = "point"
    x: float
    y: float


class PlanElement(BaseModel):
    """Элемент плана."""
    id: str
    type: str
    geometry: Union[WallGeometry, PolygonGeometry, PointGeometry]
    role: Optional[Literal["EXISTING", "TO_DELETE", "NEW", "MODIFIED"]] = None
    loadBearing: Optional[bool] = None
    thickness: Optional[float] = None
    zoneType: Optional[str] = None
    relatedTo: Optional[List[str]] = None
    selected: bool = False
    
    model_config = ConfigDict(extra="allow")  # Разрешаем дополнительные поля


class Object3DPosition(BaseModel):
    """Позиция 3D объекта."""
    x: float
    y: float
    z: float


class Object3DSize(BaseModel):
    """Размер 3D объекта."""
    x: float
    y: float
    z: float


class Object3DRotation(BaseModel):
    """Поворот 3D объекта."""
    x: float = 0
    y: float = 0
    z: float = 0


class Object3D(BaseModel):
    """3D объект (стул, стол, кровать, окно, дверь)."""
    id: str
    type: Literal["chair", "table", "bed", "window", "door"]
    position: Object3DPosition
    size: Optional[Object3DSize] = None
    rotation: Optional[Object3DRotation] = None
    wallId: Optional[str] = None
    zoneId: Optional[str] = None
    selected: bool = False
    meta: Optional[Dict[str, Any]] = None


class Plan(BaseModel):
    """План помещения."""
    meta: PlanMeta
    elements: List[PlanElement] = Field(default_factory=list)
    objects3d: Optional[List[Object3D]] = Field(default_factory=list)


class OrderPlanVersion(BaseModel):
    """Версия плана заказа."""
    id: str
    orderId: str
    versionType: Literal["ORIGINAL", "MODIFIED"]
    plan: Plan
    comment: Optional[str] = None
    createdById: Optional[str] = None
    createdAt: datetime
    
    # Для обратной совместимости: извлекаем selected_elements из элементов плана
    @property
    def selected_elements(self) -> List[str]:
        """Получает список ID выделенных элементов."""
        selected = []
        for element in self.plan.elements:
            if element.selected:
                selected.append(element.id)
        for obj3d in self.plan.objects3d or []:
            if obj3d.selected:
                selected.append(obj3d.id)
        return selected


# Для обратной совместимости создаем алиас
KanvaPlan = OrderPlanVersion
