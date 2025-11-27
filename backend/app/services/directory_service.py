from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.directory import Department, District, HouseType, Service
from app.schemas.directory import (
    DepartmentCreate,
    DepartmentUpdate,
    DistrictCreate,
    DistrictUpdate,
    HouseTypeCreate,
    HouseTypeUpdate,
    ServiceCreate,
    ServiceUpdate,
)


def upsert_department(db: Session, data: DepartmentCreate | DepartmentUpdate, code: str | None = None) -> Department:
    dept_code = code or getattr(data, "code", None)
    if dept_code is None:
        raise ValueError("Department code is required")
    department = db.get(Department, dept_code) or Department(code=dept_code)
    if isinstance(data, (DepartmentCreate, DepartmentUpdate)):
        if data.name is not None:
            department.name = data.name
        if data.description is not None:
            department.description = data.description
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def list_departments(db: Session) -> list[Department]:
    return list(db.scalars(select(Department)))


def upsert_service(db: Session, data: ServiceCreate | ServiceUpdate, code: str | None = None) -> Service:
    svc_code = code or getattr(data, "code", None)
    if svc_code is None:
        raise ValueError("Service code is required")
    service = db.get(Service, svc_code) or Service(code=svc_code)
    if getattr(data, "title", None) is not None:
        service.title = data.title
    description = getattr(data, "description", None)
    if description is not None:
        service.description = description
    if hasattr(data, "base_price") and data.base_price is not None:
        service.base_price = data.base_price
    if hasattr(data, "department_code") and data.department_code is not None:
        service.department_code = data.department_code
    if hasattr(data, "base_duration_days") and data.base_duration_days is not None:
        service.base_duration_days = data.base_duration_days
    if hasattr(data, "required_docs") and data.required_docs is not None:
        service.required_docs = data.required_docs
    if hasattr(data, "is_active") and data.is_active is not None:
        service.is_active = data.is_active
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def list_services(db: Session) -> list[Service]:
    return list(db.scalars(select(Service)))


def get_service(db: Session, code: int) -> Service | None:
    return db.get(Service, code)


def upsert_district(db: Session, data: DistrictCreate | DistrictUpdate, code: str | None = None) -> District:
    district_code = code or getattr(data, "code", None)
    if district_code is None:
        raise ValueError("District code is required")
    district = db.get(District, district_code) or District(code=district_code)
    if data.name is not None:
        district.name = data.name
    if hasattr(data, "price_coef") and data.price_coef is not None:
        district.price_coef = data.price_coef
    db.add(district)
    db.commit()
    db.refresh(district)
    return district


def list_districts(db: Session) -> list[District]:
    return list(db.scalars(select(District)))


def get_district(db: Session, code: str) -> District | None:
    return db.get(District, code)


def upsert_house_type(db: Session, data: HouseTypeCreate | HouseTypeUpdate, code: str | None = None) -> HouseType:
    house_code = code or getattr(data, "code", None)
    if house_code is None:
        raise ValueError("House type code is required")
    house_type = db.get(HouseType, house_code) or HouseType(code=house_code)
    if data.name is not None:
        house_type.name = data.name
    description = getattr(data, "description", None)
    if description is not None:
        house_type.description = description
    if hasattr(data, "price_coef") and data.price_coef is not None:
        house_type.price_coef = data.price_coef
    db.add(house_type)
    db.commit()
    db.refresh(house_type)
    return house_type


def list_house_types(db: Session) -> list[HouseType]:
    return list(db.scalars(select(HouseType)))


def get_house_type(db: Session, code: str) -> HouseType | None:
    return db.get(HouseType, code)
