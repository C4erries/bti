from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.pricing import PriceCalculatorInput, PriceEstimateResponse
from app.services.price_calculator import calculate_price

router = APIRouter(tags=["Public"])


@router.post("/calc/estimate", response_model=PriceEstimateResponse)
def calc_estimate(payload: PriceCalculatorInput, db: Session = Depends(get_db_session)):
    estimated, breakdown = calculate_price(
        db=db,
        district_code=payload.district_code,
        house_type_code=payload.house_type_code,
        calculator_input=payload.calculator_input or {},
    )
    return PriceEstimateResponse(estimatedPrice=estimated, breakdown=breakdown)
