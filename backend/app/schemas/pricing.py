from pydantic import BaseModel, ConfigDict, Field


class PriceCalculatorInput(BaseModel):
    district_code: str | None = Field(default=None, alias="districtCode")
    house_type_code: str | None = Field(default=None, alias="houseTypeCode")
    calculator_input: dict | None = Field(default=None, alias="calculatorInput")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "districtCode": "central",
                "houseTypeCode": "panel",
                "calculatorInput": {
                    "area": 52.3,
                    "works": {
                        "walls": True,
                        "wet_zone": True,
                        "doorways": False,
                    },
                    "features": {
                        "basement": False,
                        "join_apartments": True,
                    },
                    "urgent": True,
                    "notes": "Комментарий клиента о перепланировке",
                },
            }
        },
    )


class PriceBreakdown(BaseModel):
    base_component: float = Field(alias="baseComponent")
    works_component: float = Field(alias="worksComponent")
    features_coef: float = Field(alias="featuresCoef")
    raw: dict | None = None

    model_config = ConfigDict(populate_by_name=True)


class PriceEstimateResponse(BaseModel):
    estimated_price: float = Field(alias="estimatedPrice")
    breakdown: PriceBreakdown

    model_config = ConfigDict(populate_by_name=True)
