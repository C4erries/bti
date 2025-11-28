from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.directory import District, HouseType, Service
from app.models.order import Order
from app.schemas.pricing import PriceBreakdown


def calculate_price(
    db: Session,
    service_code: int,
    district_code: str | None,
    house_type_code: str | None,
    calculator_input: dict | None,
) -> tuple[float, PriceBreakdown]:
    calc = calculator_input or {}

    service = db.get(Service, service_code) if service_code else None
    base = float(service.base_price) if service and service.base_price is not None else 0.0

    district_coef = 1.0
    if district_code:
        district = db.get(District, district_code)
        if district and district.price_coef is not None:
            district_coef = float(district.price_coef)

    house_coef = 1.0
    if house_type_code:
        house = db.get(HouseType, house_type_code)
        if house and house.price_coef is not None:
            house_coef = float(house.price_coef)

    base_component = base * district_coef * house_coef

    area = float(calc.get("area") or 0)
    price_per_m2 = 500.0
    area_cost = area * price_per_m2

    works = calc.get("works") or {}
    works_cost = 0.0
    if works.get("walls"):
        works_cost += 3000
    if works.get("wet_zone"):
        works_cost += 7000
    if works.get("doorways"):
        works_cost += 5000
    works_component = area_cost + works_cost

    features = calc.get("features") or {}
    coef_features = 1.0
    if features.get("basement"):
        coef_features *= 1.2
    if features.get("join_apartments"):
        coef_features *= 1.5
    if calc.get("urgent"):
        coef_features *= 1.3

    estimated = (base_component + works_component) * coef_features
    breakdown = PriceBreakdown(
        baseComponent=round(base_component, 2),
        worksComponent=round(works_component, 2),
        featuresCoef=round(coef_features, 2),
        raw=calc,
    )
    return round(estimated, 2), breakdown


def calculate_order_price(
    db: Session,
    order: Order,
    calculator_input: dict | None = None,
) -> tuple[float | None, float | None]:
    try:
        estimated, _ = calculate_price(
            db=db,
            service_code=order.service_code,
            district_code=order.district_code,
            house_type_code=order.house_type_code,
            calculator_input=calculator_input or {},
        )
        return estimated, None
    except Exception:
        return None, None
