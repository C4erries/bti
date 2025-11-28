from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.directory import District, HouseType, Service
from app.models.order import Order


def calculate_order_price(
    db: Session,
    order: Order,
    calculator_input: dict | None = None,
) -> tuple[float | None, float | None]:
    try:
        calc = calculator_input or {}

        # base component
        service = db.get(Service, order.service_code) if order.service_code else None
        base = float(service.base_price) if service and service.base_price is not None else 0.0

        district_coef = 1.0
        if order.district_code:
            district = db.get(District, order.district_code)
            if district and district.price_coef is not None:
                district_coef = float(district.price_coef)

        house_coef = 1.0
        if order.house_type_code:
            house = db.get(HouseType, order.house_type_code)
            if house and house.price_coef is not None:
                house_coef = float(house.price_coef)

        base_component = base * district_coef * house_coef

        # works component
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

        # features coef
        features = calc.get("features") or {}
        coef_features = 1.0
        if features.get("basement"):
            coef_features *= 1.2
        if features.get("join_apartments"):
            coef_features *= 1.5
        if calc.get("urgent"):
            coef_features *= 1.3

        base_sum = base_component + works_component
        estimated = base_sum * coef_features
        return round(estimated, 2), None
    except Exception:
        return None, None
