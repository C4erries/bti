from __future__ import annotations

from collections import Counter
from typing import Any


def summarize_plan(plan: dict[str, Any] | None) -> str:
    """Build a short human-readable description of the plan for LLM prompts."""
    if not plan:
        return "План отсутствует."

    meta = plan.get("meta") or {}
    width = meta.get("width")
    height = meta.get("height")
    unit = meta.get("unit") or "px"
    scale = meta.get("scale") or {}
    px_per_meter = scale.get("px_per_meter") or scale.get("pxPerMeter")

    elements = plan.get("elements") or []
    types_counter: Counter[str] = Counter()
    role_counter: Counter[str] = Counter()
    zones_counter: Counter[str] = Counter()
    load_bearing = 0

    for elem in elements:
        elem_type = str(elem.get("type") or "unknown")
        types_counter[elem_type] += 1
        role = elem.get("role")
        if role:
            role_counter[str(role)] += 1
        if elem_type == "wall" and elem.get("loadBearing"):
            load_bearing += 1
        if elem_type == "zone":
            zones_counter[str(elem.get("zoneType") or "zone")] += 1

    lines: list[str] = []
    if width and height:
        lines.append(f"Размеры: {width} x {height} {unit}")
    if px_per_meter:
        lines.append(f"Масштаб: {px_per_meter} px за метр")
    if types_counter:
        type_parts = ", ".join(f"{t}: {c}" for t, c in types_counter.items())
        lines.append(f"Элементы: {type_parts}")
    if load_bearing:
        lines.append(f"Несущих стен: {load_bearing}")
    if zones_counter:
        zone_parts = ", ".join(f"{z}: {c}" for z, c in zones_counter.items())
        lines.append(f"Зоны: {zone_parts}")
    if role_counter:
        role_parts = ", ".join(f"{r}: {c}" for r, c in role_counter.items())
        lines.append(f"Статусы элементов: {role_parts}")

    return "\n".join(lines) or "Нет данных по плану."
