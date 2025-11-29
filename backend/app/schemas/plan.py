from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlanScale(BaseModel):
    px_per_meter: float = Field(alias="px_per_meter", gt=0)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PlanBackground(BaseModel):
    file_id: str = Field(alias="file_id")
    opacity: float = Field(ge=0, le=1)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PlanMeta(BaseModel):
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    unit: Literal["px"]
    scale: PlanScale | None = None
    background: PlanBackground | None = None
    ceiling_height_m: float | None = Field(default=None, ge=1.8, le=5, alias="ceiling_height_m")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class ElementStyle(BaseModel):
    color: str | None = Field(
        default=None,
        pattern=r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})$",
        description="HEX color (#RRGGBB or #RRGGBBAA)",
    )
    textureUrl: str | None = Field(default=None, alias="textureUrl")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class Opening(BaseModel):
    id: str
    type: Literal["door", "window", "arch", "custom"]
    from_m: float = Field(alias="from_m", ge=0)
    to_m: float = Field(alias="to_m", ge=0)
    bottom_m: float = Field(alias="bottom_m", ge=0)
    top_m: float = Field(alias="top_m", ge=0)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class WallGeometry(BaseModel):
    kind: Literal["segment"] = "segment"
    points: list[float] = Field(min_length=4, max_length=4)
    openings: list[Opening] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PolygonGeometry(BaseModel):
    kind: Literal["polygon"] = "polygon"
    points: list[float] = Field(min_length=6)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PointGeometry(BaseModel):
    kind: Literal["point"] = "point"
    x: float
    y: float

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


PlanGeometryType = WallGeometry | PolygonGeometry | PointGeometry


class PlanElementBase(BaseModel):
    id: str
    type: str
    role: Literal["EXISTING", "TO_DELETE", "NEW", "MODIFIED"] | None = None
    loadBearing: bool | None = Field(default=None, alias="loadBearing")
    thickness: float | None = None
    zoneType: str | None = Field(default=None, alias="zoneType")
    relatedTo: list[str] | None = Field(default=None, alias="relatedTo")
    selected: bool = False
    style: ElementStyle | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class WallElement(PlanElementBase):
    type: Literal["wall"] = "wall"
    geometry: WallGeometry

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ZoneElement(PlanElementBase):
    type: Literal["zone"] = "zone"
    geometry: PolygonGeometry

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DoorElement(PlanElementBase):
    type: Literal["door"] = "door"
    geometry: WallGeometry

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class WindowElement(PlanElementBase):
    type: Literal["window"] = "window"
    geometry: WallGeometry

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class LabelElement(PlanElementBase):
    type: Literal["label"] = "label"
    text: str
    geometry: PointGeometry

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Vec3(BaseModel):
    x: float
    y: float
    z: float

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class Rotation3(BaseModel):
    x: float = 0
    y: float = 0
    z: float = 0

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PlanObject3D(BaseModel):
    id: str
    type: Literal["chair", "table", "bed", "window", "door"]
    position: Vec3
    size: Vec3 | None = None
    rotation: Rotation3 | None = None
    wallId: str | None = Field(default=None, alias="wallId")
    zoneId: str | None = Field(default=None, alias="zoneId")
    selected: bool = False
    meta: dict | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


PlanElement = WallElement | ZoneElement | DoorElement | WindowElement | LabelElement


class Plan(BaseModel):
    meta: PlanMeta
    elements: list[PlanElement]
    objects3d: list[PlanObject3D] | None = Field(default=None, alias="objects3d")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
