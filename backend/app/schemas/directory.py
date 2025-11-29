from pydantic import BaseModel, ConfigDict, Field


class DepartmentBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)


class DistrictBase(BaseModel):
    code: str
    name: str
    price_coef: float | None = Field(default=1.0, alias="priceCoef")

    model_config = ConfigDict(populate_by_name=True)


class DistrictCreate(DistrictBase):
    pass


class DistrictUpdate(BaseModel):
    name: str | None = None
    price_coef: float | None = Field(default=None, alias="priceCoef")

    model_config = ConfigDict(populate_by_name=True)


class DistrictRead(DistrictBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HouseTypeBase(BaseModel):
    code: str
    name: str
    price_coef: float | None = Field(default=1.0, alias="priceCoef")

    model_config = ConfigDict(populate_by_name=True)


class HouseTypeCreate(HouseTypeBase):
    pass


class HouseTypeUpdate(BaseModel):
    name: str | None = None
    price_coef: float | None = Field(default=None, alias="priceCoef")

    model_config = ConfigDict(populate_by_name=True)


class HouseTypeRead(HouseTypeBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
