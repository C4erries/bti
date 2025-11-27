from pydantic import BaseModel, ConfigDict


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
    code: str
    name: str
    description: str | None = None
    base_price: float | None = None
    department_code: str | None = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_price: float | None = None
    department_code: str | None = None


class ServiceRead(ServiceBase):
    model_config = ConfigDict(from_attributes=True)


class DistrictBase(BaseModel):
    code: str
    name: str
    coefficient: float = 1.0


class DistrictCreate(DistrictBase):
    pass


class DistrictUpdate(BaseModel):
    name: str | None = None
    coefficient: float | None = None


class DistrictRead(DistrictBase):
    model_config = ConfigDict(from_attributes=True)


class HouseTypeBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    coefficient: float = 1.0


class HouseTypeCreate(HouseTypeBase):
    pass


class HouseTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    coefficient: float | None = None


class HouseTypeRead(HouseTypeBase):
    model_config = ConfigDict(from_attributes=True)
