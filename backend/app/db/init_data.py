from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.directory import (
    DepartmentCreate,
    DistrictCreate,
    HouseTypeCreate,
    ServiceCreate,
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
        DistrictCreate(code="central", name="Central", priceCoef=1.2),
        DistrictCreate(code="north", name="North", priceCoef=1.0),
        DistrictCreate(code="south", name="South", priceCoef=0.9),
    ]
    for dist in districts:
        directory_service.upsert_district(db, dist)

    house_types = [
        HouseTypeCreate(code="panel", name="Panel building", priceCoef=1.0),
        HouseTypeCreate(code="brick", name="Brick building", priceCoef=1.1),
    ]
    for ht in house_types:
        directory_service.upsert_house_type(db, ht)

    services = [
        ServiceCreate(
            code=1,
            title="BTI plan",
            department_code="BTI",
            base_price=5000,
            description="Measurements and BTI documentation",
        ),
        ServiceCreate(
            code=2,
            title="Remodel approval",
            department_code="CAD",
            base_price=12000,
            description="Support for approval of remodelling",
        ),
    ]
    for svc in services:
        directory_service.upsert_service(db, svc)


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
            service_code=1,
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
                "scale": {"px_per_meter": 40},
                "background": None,
            },
            "elements": [
                {
                    "id": "wall_1",
                    "type": "wall",
                    "role": "EXISTING",
                    "loadBearing": True,
                    "thickness": 20,
                    "geometry": {
                        "kind": "segment",
                        "points": [100, 100, 700, 100],
                    },
                },
                {
                    "id": "zone_kitchen",
                    "type": "zone",
                    "zoneType": "kitchen",
                    "relatedTo": ["wall_1"],
                    "geometry": {
                        "kind": "polygon",
                        "points": [100, 100, 500, 100, 500, 350, 100, 350],
                    },
                },
            ],
            "objects3d": [
                {
                    "id": "obj_sofa_1",
                    "type": "sofa",
                    "position": {"x": 3.2, "y": 0.0, "z": 1.5},
                    "rotation": {"y": 1.57},
                    "size": {"x": 2.0, "y": 0.8, "z": 0.9},
                }
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
