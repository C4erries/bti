from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.directory import (
    DepartmentCreate,
    DistrictCreate,
    HouseTypeCreate,
)
from app.schemas.orders import CreateOrderRequest, SavePlanChangesRequest
from app.schemas.user import ExecutorCreateRequest, UserCreate
from app.services import directory_service, order_service, user_service
from app.models.order import OrderPlanVersion


def init_directories(db: Session):
    departments = [
        DepartmentCreate(code="GEO", name="Geodesy", description="Geodesy works"),
        DepartmentCreate(code="BTI", name="BTI", description="Inventory and plans"),
        DepartmentCreate(code="CAD", name="Cadastre", description="Cadastre and permits"),
    ]
    for dept in departments:
        directory_service.upsert_department(db, dept)

    districts = [
        DistrictCreate(code="central", name="Центральный", priceCoef=1.2),
        DistrictCreate(code="west", name="Западный", priceCoef=1.0),
        DistrictCreate(code="prikub", name="Прикубанский", priceCoef=1.0),
        DistrictCreate(code="karasun", name="Карасунский", priceCoef=1.0),
    ]
    for dist in districts:
        directory_service.upsert_district(db, dist)

    house_types = [
        HouseTypeCreate(code="panel", name="Панельный дом", priceCoef=1.0),
        HouseTypeCreate(code="brick", name="Кирпичный дом", priceCoef=1.1),
    ]
    for ht in house_types:
        directory_service.upsert_house_type(db, ht)


def init_users(db: Session):
    client_email = "client@example.com"
    executor_email = "executor@example.com"
    if not user_service.get_user_by_email(db, client_email):
        user_service.create_client(
            db,
            UserCreate(
                email=client_email,
                password="client123",
                full_name="Test Client",
                phone="+70000000001",
            ),
        )
    if not user_service.get_user_by_email(db, executor_email):
        user_service.create_executor(
            db,
            ExecutorCreateRequest(
                email=executor_email,
                password="executor123",
                full_name="Test Executor",
                phone="+70000000002",
                department_code="BTI",
                experience_years=5,
                specialization="Measurements",
            ),
        )
    if not user_service.get_user_by_email(db, "admin@example.com"):
        user_service.create_user(
            db,
            UserCreate(
                email="admin@example.com",
                password="admin123",
                full_name="Admin",
                phone="+70000000000",
                is_admin=True,
            ),
        )
    if not user_service.get_user_by_email(db, "superadmin@example.com"):
        user_service.create_user(
            db,
            UserCreate(
                email="superadmin@example.com",
                password="superadmin123",
                full_name="Super Admin",
                phone="+70000000003",
                is_admin=True,
                is_superadmin=True,
            ),
        )


def init_orders(db: Session):
    client = user_service.get_user_by_email(db, "client@example.com")
    executor = user_service.get_user_by_email(db, "executor@example.com")
    if not client or not executor:
        return
    existing = order_service.get_client_orders(db, client.id)
    if existing:
        return
    order = order_service.create_order(
        db,
        client=client,
        data=CreateOrderRequest(
            title="BTI plan for remodel",
            description="Need measurements and technical plan",
            address="Sample address 1",
            district_code="central",
            house_type_code="brick",
            calculator_input={"rooms": 2},
        ),
    )
    order_service.assign_executor(db, order, executor, assigned_by=executor)


def init_demo_plan3d(db: Session):
    client = user_service.get_user_by_email(db, "client@example.com")
    if not client:
        return
    orders = order_service.get_client_orders(db, client.id)
    if not orders:
        return
    order = orders[0]
    existing = db.scalar(select(OrderPlanVersion).where(OrderPlanVersion.order_id == order.id))
    if existing:
        return

    payload = SavePlanChangesRequest(
        versionType="MODIFIED",
        plan={
            "meta": {
                "width": 800,
                "height": 600,
                "unit": "px",
                "scale": {"px_per_meter": 100},
                "background": None,
                "ceiling_height_m": 2.7,
            },
            "elements": [
                {
                    "id": "wall_top",
                    "type": "wall",
                    "role": "EXISTING",
                    "loadBearing": True,
                    "thickness": 20,
                    "geometry": {
                        "kind": "segment",
                        "points": [100, 100, 700, 100],
                        "openings": [
                            {
                                "id": "window_living",
                                "type": "window",
                                "from_m": 3.9,
                                "to_m": 5.1,
                                "bottom_m": 0.9,
                                "top_m": 2.1,
                            }
                        ],
                    },
                },
                {
                    "id": "wall_right",
                    "type": "wall",
                    "role": "EXISTING",
                    "loadBearing": True,
                    "thickness": 20,
                    "geometry": {
                        "kind": "segment",
                        "points": [700, 100, 700, 400],
                    },
                },
                {
                    "id": "wall_bottom",
                    "type": "wall",
                    "role": "EXISTING",
                    "loadBearing": True,
                    "thickness": 20,
                    "geometry": {
                        "kind": "segment",
                        "points": [100, 400, 700, 400],
                        "openings": [
                            {
                                "id": "door_entrance",
                                "type": "door",
                                "from_m": 0.55,
                                "to_m": 1.45,
                                "bottom_m": 0.0,
                                "top_m": 2.0,
                            }
                        ],
                    },
                },
                {
                    "id": "wall_left",
                    "type": "wall",
                    "role": "EXISTING",
                    "loadBearing": True,
                    "thickness": 20,
                    "geometry": {
                        "kind": "segment",
                        "points": [100, 400, 100, 100],
                    },
                },
                {
                    "id": "wall_middle",
                    "type": "wall",
                    "role": "EXISTING",
                    "loadBearing": False,
                    "thickness": 15,
                    "geometry": {
                        "kind": "segment",
                        "points": [400, 100, 400, 400],
                        "openings": [
                            {
                                "id": "door_between_rooms",
                                "type": "door",
                                "from_m": 1.55,
                                "to_m": 2.45,
                                "bottom_m": 0.0,
                                "top_m": 2.0,
                            }
                        ],
                    },
                },
                {
                    "id": "zone_bedroom",
                    "type": "zone",
                    "role": "EXISTING",
                    "zoneType": "bedroom",
                    "relatedTo": ["wall_top", "wall_left", "wall_bottom", "wall_middle"],
                    "selected": True,
                    "geometry": {
                        "kind": "polygon",
                        "points": [
                            100,
                            100,
                            400,
                            100,
                            400,
                            400,
                            100,
                            400,
                        ],
                    },
                },
                {
                    "id": "zone_living",
                    "type": "zone",
                    "role": "EXISTING",
                    "zoneType": "living_room",
                    "relatedTo": ["wall_top", "wall_middle", "wall_right", "wall_bottom"],
                    "selected": True,
                    "geometry": {
                        "kind": "polygon",
                        "points": [
                            400,
                            100,
                            700,
                            100,
                            700,
                            400,
                            400,
                            400,
                        ],
                    },
                },
                {
                    "id": "label_bedroom",
                    "type": "label",
                    "role": "EXISTING",
                    "selected": True,
                    "text": "Bedroom",
                    "geometry": {"kind": "point", "x": 250, "y": 230},
                },
                {
                    "id": "label_living",
                    "type": "label",
                    "role": "EXISTING",
                    "selected": False,
                    "text": "Living room",
                    "geometry": {"kind": "point", "x": 550, "y": 230},
                },
            ],
            "objects3d": [
                {
                    "id": "bed_1",
                    "type": "bed",
                    "position": {"x": 1.5, "y": 0.0, "z": 1.5},
                    "size": {"x": 2.0, "y": 0.6, "z": 1.6},
                    "rotation": {"x": 0.0, "y": 1.57, "z": 0.0},
                    "wallId": None,
                    "zoneId": "zone_bedroom",
                    "selected": True,
                    "meta": {"note": "Кровать в спальне"},
                },
                {
                    "id": "table_1",
                    "type": "table",
                    "position": {"x": 4.5, "y": 0.0, "z": 1.8},
                    "size": {"x": 1.6, "y": 0.75, "z": 0.9},
                    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "wallId": None,
                    "zoneId": "zone_living",
                    "selected": False,
                    "meta": {"usage": "dining"},
                },
                {
                    "id": "chair_1",
                    "type": "chair",
                    "position": {"x": 4.0, "y": 0.0, "z": 1.4},
                    "size": {"x": 0.6, "y": 0.9, "z": 0.6},
                    "rotation": {"x": 0.0, "y": 0.3, "z": 0.0},
                    "wallId": None,
                    "zoneId": "zone_living",
                    "selected": True,
                    "meta": {"note": "Стул у стола (левый)"},
                },
                {
                    "id": "chair_2",
                    "type": "chair",
                    "position": {"x": 5.0, "y": 0.0, "z": 1.4},
                    "size": {"x": 0.6, "y": 0.9, "z": 0.6},
                    "rotation": {"x": 0.0, "y": -0.3, "z": 0.0},
                    "wallId": None,
                    "zoneId": "zone_living",
                    "selected": False,
                    "meta": {"note": "Стул у стола (правый)"},
                },
                {
                    "id": "door_entrance",
                    "type": "door",
                    "position": {"x": 1.0, "y": 0.0, "z": 3.0},
                    "size": {"x": 0.9, "y": 2.0, "z": 0.1},
                    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "wallId": "wall_bottom",
                    "zoneId": "zone_living",
                    "selected": True,
                    "meta": {"openingDirection": "inside"},
                },
                {
                    "id": "door_between_rooms",
                    "type": "door",
                    "position": {"x": 4.0, "y": 0.0, "z": 2.0},
                    "size": {"x": 0.9, "y": 2.0, "z": 0.1},
                    "rotation": {"x": 0.0, "y": 1.57, "z": 0.0},
                    "wallId": "wall_middle",
                    "zoneId": "zone_living",
                    "selected": True,
                    "meta": {"openingDirection": "to_living"},
                },
                {
                    "id": "window_living",
                    "type": "window",
                    "position": {"x": 5.0, "y": 1.4, "z": 0.0},
                    "size": {"x": 1.2, "y": 1.2, "z": 0.1},
                    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "wallId": "wall_top",
                    "zoneId": "zone_living",
                    "selected": False,
                    "meta": {"isBalcony": False},
                },
            ],
        },
    )
    order_service.add_plan_version(db, order, payload)


def init_data():
    db = SessionLocal()
    try:
        init_directories(db)
        init_users(db)
        init_orders(db)
        init_demo_plan3d(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_data()
