from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlanScale(BaseModel):
    px_per_meter: float = Field(alias="px_per_meter", gt=0)

    model_config = ConfigDict(populate_by_name=True)


class PlanBackground(BaseModel):
    file_id: str = Field(alias="file_id")
    opacity: float = Field(ge=0, le=1)

    model_config = ConfigDict(populate_by_name=True)


class PlanMeta(BaseModel):
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    unit: Literal["px"]
    scale: PlanScale | None = None
    background: PlanBackground | None = None

    model_config = ConfigDict(populate_by_name=True)


class SegmentGeometry(BaseModel):
    kind: Literal["segment"] = "segment"
    points: list[float] = Field(min_length=4)

    model_config = ConfigDict(populate_by_name=True)


class PolygonGeometry(BaseModel):
    kind: Literal["polygon"] = "polygon"
    points: list[float] = Field(min_length=6)

    model_config = ConfigDict(populate_by_name=True)


class PointGeometry(BaseModel):
    kind: Literal["point"] = "point"
    x: float
    y: float

    model_config = ConfigDict(populate_by_name=True)


class PlanElementBase(BaseModel):
    id: str
    type: Literal["wall", "zone", "door", "window", "label"]

    model_config = ConfigDict(populate_by_name=True)


class WallElement(PlanElementBase):
    type: Literal["wall"] = "wall"
    role: Literal["EXISTING", "TO_DELETE", "NEW", "MODIFIED"]
    loadBearing: bool | None = Field(default=None, alias="loadBearing")
    thickness: float | None = None
    geometry: SegmentGeometry

    model_config = ConfigDict(populate_by_name=True)


class ZoneElement(PlanElementBase):
    type: Literal["zone"] = "zone"
    zoneType: Literal[
        "wet",
        "living_room",
        "dining_room",
        "kitchen",
        "entrance_hall",
        "bathroom",
        "laundry_room",
        "bedroom",
        "kids_room",
        "wardrobe",
        "home_office",
        "balcony",
        "veranda",
        "loggia",
    ] = Field(alias="zoneType")
    relatedTo: list[str] | None = Field(default=None, alias="relatedTo")
    geometry: PolygonGeometry

    model_config = ConfigDict(populate_by_name=True)


class DoorElement(PlanElementBase):
    type: Literal["door"] = "door"
    role: Literal["EXISTING", "TO_DELETE", "NEW", "MODIFIED"]
    geometry: SegmentGeometry

    model_config = ConfigDict(populate_by_name=True)


class WindowElement(PlanElementBase):
    type: Literal["window"] = "window"
    role: Literal["EXISTING", "TO_DELETE", "NEW", "MODIFIED"]
    windowType: Literal["STANDARD", "BALCONY_DOOR", "PANORAMIC", "ROOF", "OTHER"] = Field(
        default="STANDARD", alias="windowType"
    )
    sillHeight_m: float | None = Field(default=None, alias="sillHeight_m")
    geometry: SegmentGeometry

    model_config = ConfigDict(populate_by_name=True)


class LabelElement(PlanElementBase):
    type: Literal["label"] = "label"
    text: str
    geometry: PointGeometry

    model_config = ConfigDict(populate_by_name=True)


PlanElement = WallElement | ZoneElement | DoorElement | WindowElement | LabelElement


class PlanObject3D(BaseModel):
    id: str
    type: str
    position: dict
    rotation: dict | None = None
    size: dict | None = None

    model_config = ConfigDict(populate_by_name=True)


class Plan(BaseModel):
    meta: PlanMeta
    elements: list[PlanElement]
    objects3d: list[PlanObject3D] | None = Field(default=None, alias="objects3d")

    model_config = ConfigDict(populate_by_name=True)
