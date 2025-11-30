"""Сервис для обработки планов из фотографий."""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from ...infrastructure.config import load_config
from v2.models.plan import OrderPlanVersion, Plan, PlanMeta, PlanElement, Object3D
from .cubicasa_client import CubiCasaClient, CubiCasaProcessingError


async def process_plan_from_image(
    image_bytes: bytes,
    order_id: Optional[str] = None,
    version_type: str = "ORIGINAL",
    px_per_meter: Optional[float] = None,
    cubicasa_api_url: Optional[str] = None
) -> OrderPlanVersion:
    """
    Обработка изображения планировки и получение структурированного плана.
    
    Args:
        image_bytes: Байты изображения планировки
        order_id: ID заказа (будет сгенерирован если не указан)
        version_type: Тип версии ("ORIGINAL" или "MODIFIED")
        px_per_meter: Пикселей на метр для масштабирования
        cubicasa_api_url: URL API CubiCasa5K (опционально, по умолчанию из конфига)
        
    Returns:
        OrderPlanVersion: Структурированный план в формате 3Dmodel_schema.json
        
    Raises:
        CubiCasaProcessingError: При ошибке обработки
    """
    # Генерируем order_id если не указан
    if not order_id:
        order_id = str(uuid.uuid4())
    
    # Создаем клиент
    client = CubiCasaClient(base_url=cubicasa_api_url)
    
    # Обрабатываем изображение через API
    result = await client.process_image(
        image_bytes=image_bytes,
        order_id=order_id,
        version_type=version_type,
        px_per_meter=px_per_meter
    )
    
    # Конвертируем результат в OrderPlanVersion
    return _convert_api_response_to_plan(result)


def _convert_api_response_to_plan(api_response: Dict[str, Any]) -> OrderPlanVersion:
    """
    Конвертация ответа API в OrderPlanVersion.
    
    Args:
        api_response: Ответ от API в формате 3Dmodel_schema.json
        
    Returns:
        OrderPlanVersion: Структурированный план
    """
    plan_data = api_response.get("plan", {})
    meta_data = plan_data.get("meta", {})
    
    # Создаем PlanMeta
    plan_meta = PlanMeta(
        width=meta_data.get("width", 0),
        height=meta_data.get("height", 0),
        unit=meta_data.get("unit", "px"),
        scale=None,  # Будет обработано ниже
        background=None,  # Будет обработано ниже
        ceiling_height_m=meta_data.get("ceiling_height_m")
    )
    
    # Обрабатываем scale
    if "scale" in meta_data and meta_data["scale"]:
        from v2.models.plan import PlanScale
        plan_meta.scale = PlanScale(
            px_per_meter=meta_data["scale"]["px_per_meter"]
        )
    
    # Обрабатываем background
    if "background" in meta_data and meta_data["background"]:
        from v2.models.plan import PlanBackground
        plan_meta.background = PlanBackground(
            file_id=meta_data["background"]["file_id"],
            opacity=meta_data["background"]["opacity"]
        )
    
    # Обрабатываем elements
    elements = []
    for elem_data in plan_data.get("elements", []):
        element = _convert_element(elem_data)
        if element:
            elements.append(element)
    
    # Обрабатываем objects3d
    objects3d = []
    for obj_data in plan_data.get("objects3d", []):
        obj3d = _convert_object3d(obj_data)
        if obj3d:
            objects3d.append(obj3d)
    
    # Создаем Plan
    plan = Plan(
        meta=plan_meta,
        elements=elements,
        objects3d=objects3d if objects3d else None
    )
    
    # Создаем OrderPlanVersion
    return OrderPlanVersion(
        id=api_response.get("id", str(uuid.uuid4())),
        orderId=api_response.get("orderId", str(uuid.uuid4())),
        versionType=api_response.get("versionType", "ORIGINAL"),
        plan=plan,
        comment=api_response.get("comment"),
        createdById=api_response.get("createdById"),
        createdAt=datetime.fromisoformat(
            api_response.get("createdAt", datetime.now().isoformat())
        )
    )


def _convert_element(elem_data: Dict[str, Any]) -> Optional[PlanElement]:
    """Конвертация элемента из API ответа."""
    from v2.models.plan import (
        WallGeometry, PolygonGeometry, PointGeometry
    )
    
    geometry_data = elem_data.get("geometry", {})
    geometry_kind = geometry_data.get("kind")
    
    geometry = None
    if geometry_kind == "segment":
        geometry = WallGeometry(
            kind="segment",
            points=geometry_data.get("points", []),
            openings=None  # Будет обработано ниже
        )
        # Обрабатываем openings
        if "openings" in geometry_data and geometry_data["openings"]:
            from v2.models.plan import Opening
            openings = []
            for opening_data in geometry_data["openings"]:
                openings.append(Opening(
                    id=opening_data["id"],
                    type=opening_data["type"],
                    from_m=opening_data["from_m"],
                    to_m=opening_data["to_m"],
                    bottom_m=opening_data["bottom_m"],
                    top_m=opening_data["top_m"]
                ))
            geometry.openings = openings
    
    elif geometry_kind == "polygon":
        geometry = PolygonGeometry(
            kind="polygon",
            points=geometry_data.get("points", [])
        )
    
    elif geometry_kind == "point":
        geometry = PointGeometry(
            kind="point",
            x=geometry_data.get("x", 0),
            y=geometry_data.get("y", 0)
        )
    
    if not geometry:
        return None
    
    return PlanElement(
        id=elem_data.get("id", str(uuid.uuid4())),
        type=elem_data.get("type", "unknown"),
        geometry=geometry,
        role=elem_data.get("role"),
        loadBearing=elem_data.get("loadBearing"),
        thickness=elem_data.get("thickness"),
        zoneType=elem_data.get("zoneType"),
        relatedTo=elem_data.get("relatedTo"),
        selected=elem_data.get("selected", False)
    )


def _convert_object3d(obj_data: Dict[str, Any]) -> Optional[Object3D]:
    """Конвертация 3D объекта из API ответа."""
    from v2.models.plan import Object3DPosition, Object3DSize, Object3DRotation
    
    position_data = obj_data.get("position", {})
    position = Object3DPosition(
        x=position_data.get("x", 0),
        y=position_data.get("y", 0),
        z=position_data.get("z", 0)
    )
    
    size = None
    if "size" in obj_data and obj_data["size"]:
        size_data = obj_data["size"]
        size = Object3DSize(
            x=size_data.get("x", 0),
            y=size_data.get("y", 0),
            z=size_data.get("z", 0)
        )
    
    rotation = None
    if "rotation" in obj_data and obj_data["rotation"]:
        rotation_data = obj_data["rotation"]
        rotation = Object3DRotation(
            x=rotation_data.get("x", 0),
            y=rotation_data.get("y", 0),
            z=rotation_data.get("z", 0)
        )
    
    return Object3D(
        id=obj_data.get("id", str(uuid.uuid4())),
        type=obj_data.get("type", "chair"),
        position=position,
        size=size,
        rotation=rotation,
        wallId=obj_data.get("wallId"),
        zoneId=obj_data.get("zoneId"),
        selected=obj_data.get("selected", False),
        meta=obj_data.get("meta")
    )

