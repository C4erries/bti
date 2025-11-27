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


class ServiceBase(BaseModel):
    code: int
    title: str
    description: str | None = None
    department_code: str | None = Field(default=None, alias="departmentCode")
    base_price: float | None = Field(default=None, alias="basePrice")
    base_duration_days: int | None = Field(default=None, alias="baseDurationDays")
    required_docs: dict | None = Field(default=None, alias="requiredDocs")
    is_active: bool | None = Field(default=True, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    department_code: str | None = Field(default=None, alias="departmentCode")
    base_price: float | None = Field(default=None, alias="basePrice")
    base_duration_days: int | None = Field(default=None, alias="baseDurationDays")
    required_docs: dict | None = Field(default=None, alias="requiredDocs")
    is_active: bool | None = Field(default=None, alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class ServiceRead(ServiceBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
