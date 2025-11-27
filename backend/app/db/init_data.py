from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.directory import (
    DepartmentCreate,
    DistrictCreate,
    HouseTypeCreate,
    ServiceCreate,
)
from app.schemas.orders import OrderCreate
from app.schemas.user import ExecutorCreateRequest, UserCreate
from app.services import directory_service, order_service, user_service


def init_directories(db: Session):
    departments = [
        DepartmentCreate(code="GEO", name="Geodesy", description="Geodesy works"),
        DepartmentCreate(code="BTI", name="BTI", description="Inventory and plans"),
        DepartmentCreate(code="CAD", name="Cadastre", description="Cadastre and permits"),
    ]
    for dept in departments:
        directory_service.upsert_department(db, dept)

    districts = [
        DistrictCreate(code="central", name="Central", coefficient=1.2),
        DistrictCreate(code="north", name="North", coefficient=1.0),
        DistrictCreate(code="south", name="South", coefficient=0.9),
    ]
    for dist in districts:
        directory_service.upsert_district(db, dist)

    house_types = [
        HouseTypeCreate(code="panel", name="Panel building", coefficient=1.0),
        HouseTypeCreate(code="brick", name="Brick building", coefficient=1.1),
    ]
    for ht in house_types:
        directory_service.upsert_house_type(db, ht)

    services = [
        ServiceCreate(
            code="bti_plan",
            name="BTI plan",
            department_code="BTI",
            base_price=5000,
            description="Measurements and BTI documentation",
        ),
        ServiceCreate(
            code="replan",
            name="Remodel approval",
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
        data=OrderCreate(
            service_code="bti_plan",
            title="BTI plan for remodel",
            description="Need measurements and technical plan",
            address="Sample address 1",
            district_code="central",
            house_type_code="brick",
            area=54.5,
            calculator_input={"rooms": 2},
        ),
    )
    order_service.assign_executor(db, order, executor, assigned_by=executor)


def init_data():
    db = SessionLocal()
    try:
        init_directories(db)
        init_users(db)
        init_orders(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_data()
