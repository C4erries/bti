from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.directory import (
    DistrictRead,
    HouseTypeRead,
)
from app.services import directory_service

router = APIRouter(tags=["Public"])

@router.get("/districts", response_model=list[DistrictRead])
def list_districts(db: Session = Depends(get_db_session)):
    districts = directory_service.list_districts(db)
    return [DistrictRead.model_validate(d) for d in districts]


@router.get("/districts/{code}", response_model=DistrictRead)
def get_district(code: str, db: Session = Depends(get_db_session)):
    district = directory_service.get_district(db, code)
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return DistrictRead.model_validate(district)


@router.get("/house-types", response_model=list[HouseTypeRead])
def list_house_types(db: Session = Depends(get_db_session)):
    house_types = directory_service.list_house_types(db)
    return [HouseTypeRead.model_validate(h) for h in house_types]


@router.get("/house-types/{code}", response_model=HouseTypeRead)
def get_house_type(code: str, db: Session = Depends(get_db_session)):
    house_type = directory_service.get_house_type(db, code)
    if not house_type:
        raise HTTPException(status_code=404, detail="House type not found")
    return HouseTypeRead.model_validate(house_type)
