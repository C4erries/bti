from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.schemas.directory import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    DistrictCreate,
    DistrictRead,
    DistrictUpdate,
    HouseTypeCreate,
    HouseTypeRead,
    HouseTypeUpdate,
)
from app.services import directory_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(
    db: Session = Depends(get_db_session), admin=Depends(get_current_admin)
):
    departments = directory_service.list_departments(db)
    return [DepartmentRead.model_validate(d) for d in departments]


@router.post("/departments", response_model=DepartmentRead)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    department = directory_service.upsert_department(db, data)
    return DepartmentRead.model_validate(department)


@router.patch("/departments/{code}", response_model=DepartmentRead)
def update_department(
    code: str,
    data: DepartmentUpdate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    department = directory_service.upsert_department(db, data, code=code)
    return DepartmentRead.model_validate(department)


@router.post("/districts", response_model=DistrictRead)
def create_district(
    data: DistrictCreate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    district = directory_service.upsert_district(db, data)
    return DistrictRead.model_validate(district)


@router.patch("/districts/{code}", response_model=DistrictRead)
def update_district(
    code: str,
    data: DistrictUpdate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    district = directory_service.upsert_district(db, data, code=code)
    return DistrictRead.model_validate(district)


@router.post("/house-types", response_model=HouseTypeRead)
def create_house_type(
    data: HouseTypeCreate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    house_type = directory_service.upsert_house_type(db, data)
    return HouseTypeRead.model_validate(house_type)


@router.patch("/house-types/{code}", response_model=HouseTypeRead)
def update_house_type(
    code: str,
    data: HouseTypeUpdate,
    db: Session = Depends(get_db_session),
    admin=Depends(get_current_admin),
):
    house_type = directory_service.upsert_house_type(db, data, code=code)
    return HouseTypeRead.model_validate(house_type)
