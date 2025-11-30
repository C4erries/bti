"""Анализ планировки и оценка рисков."""

from typing import List, Dict, Any, Tuple, Optional
import sys
from pathlib import Path

# Добавляем путь к моделям
ai_app_path = Path(__file__).parent.parent.parent.parent
if str(ai_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_path))

from models.plan import KanvaPlan, WallGeometry, PolygonGeometry
from models.risks import AiRisk
from models.user import UserProfile
import sys
from pathlib import Path

# Настраиваем пути для абсолютных импортов
# Структура: ai/app/app/... поэтому добавляем ai/app/app в путь
ai_app_app_path = Path(__file__).parent.parent.parent
if str(ai_app_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_app_path))

from app.infrastructure import generate_json_with_fallback, load_config, get_logger
from app.services.embedding import generate_embedding_for_plan
from app.services.rag import retrieve_relevant_chunks, build_rag_index

logger = get_logger("analysis")


def _format_plan_for_analysis(plan: KanvaPlan) -> str:
    """
    Форматирует план для анализа в текстовый формат.
    
    Args:
        plan: План помещения (OrderPlanVersion)
        
    Returns:
        str: Текстовое представление плана для анализа
    """
    parts = []
    plan_data = plan.plan
    
    # Получаем масштаб для конвертации координат
    px_per_meter = None
    if plan_data.meta.scale:
        px_per_meter = plan_data.meta.scale.px_per_meter
    
    # Метаданные плана
    parts.append("Метаданные плана:")
    parts.append(f"- Размеры: {plan_data.meta.width}×{plan_data.meta.height} {plan_data.meta.unit}")
    if px_per_meter:
        parts.append(f"- Масштаб: {px_per_meter} px/м")
    if plan_data.meta.ceiling_height_m:
        parts.append(f"- Высота потолка: {plan_data.meta.ceiling_height_m} м")
    parts.append("")
    
    # Элементы плана
    parts.append("Элементы плана:")
    
    walls = [e for e in plan_data.elements if e.type == "wall"]
    zones = [e for e in plan_data.elements if e.type == "zone"]
    labels = [e for e in plan_data.elements if e.type == "label"]
    
    parts.append(f"- Стен: {len(walls)}")
    parts.append(f"- Зон: {len(zones)}")
    parts.append(f"- Меток: {len(labels)}")
    
    # Детали стен
    if walls:
        parts.append("")
        parts.append("Детали стен:")
        for wall in walls[:10]:
            wall_info = f"  - Стена {wall.id}"
            if wall.thickness:
                wall_info += f", толщина: {wall.thickness} м"
            if wall.loadBearing is not None:
                wall_info += f", несущая: {'да' if wall.loadBearing else 'нет'}"
            if wall.role:
                wall_info += f", роль: {wall.role}"
            if isinstance(wall.geometry, WallGeometry) and wall.geometry.openings:
                wall_info += f", проёмов: {len(wall.geometry.openings)}"
            parts.append(wall_info)
    
    # Детали зон
    if zones:
        parts.append("")
        parts.append("Детали зон:")
        for zone in zones[:10]:
            zone_info = f"  - Зона {zone.id}"
            if zone.zoneType:
                zone_info += f", тип: {zone.zoneType}"
            if zone.role:
                zone_info += f", роль: {zone.role}"
            
            # Вычисляем площадь зоны из геометрии
            if isinstance(zone.geometry, PolygonGeometry):
                points = zone.geometry.points
                if len(points) >= 6 and len(points) % 2 == 0:
                    try:
                        # Вычисляем площадь многоугольника по формуле Гаусса (Shoelace)
                        area_px = 0.0
                        num_points = len(points) // 2
                        for i in range(num_points):
                            j = (i + 1) % num_points
                            x_i, y_i = points[i * 2], points[i * 2 + 1]
                            x_j, y_j = points[j * 2], points[j * 2 + 1]
                            area_px += x_i * y_j
                            area_px -= x_j * y_i
                        area_px = abs(area_px) / 2.0
                        
                        # Конвертируем из пикселей в метры
                        if px_per_meter and px_per_meter > 0:
                            zone_area = area_px / (px_per_meter * px_per_meter)
                            zone_info += f", площадь: {zone_area:.1f} м²"
                    except Exception:
                        pass
            
            parts.append(zone_info)
    
    # Проёмы в стенах (двери и окна)
    openings_info = []
    for wall in walls:
        if isinstance(wall.geometry, WallGeometry) and wall.geometry.openings:
            for opening in wall.geometry.openings:
                opening_type = "дверь" if opening.type == "door" else "окно" if opening.type == "window" else opening.type
                openings_info.append(f"  - {opening_type} {opening.id} в стене {wall.id} (от {opening.from_m} до {opening.to_m} м, высота {opening.bottom_m}-{opening.top_m} м)")
    
    if openings_info:
        parts.append("")
        parts.append("Проёмы (двери/окна):")
        parts.extend(openings_info[:10])
    
    # 3D объекты
    if plan_data.objects3d:
        parts.append("")
        parts.append(f"3D объекты: {len(plan_data.objects3d)}")
        for obj3d in plan_data.objects3d[:10]:
            obj_info = f"  - {obj3d.type} {obj3d.id}"
            if obj3d.zoneId:
                obj_info += f", зона: {obj3d.zoneId}"
            if obj3d.wallId:
                obj_info += f", стена: {obj3d.wallId}"
            if obj3d.size:
                obj_info += f", размер: {obj3d.size.x}×{obj3d.size.y}×{obj3d.size.z} м"
            parts.append(obj_info)
    
    return "\n".join(parts)


def _build_analysis_system_prompt(
    order_context: Dict[str, Any],
    relevant_chunks: List[str],
    user_profile: Optional[UserProfile] = None
) -> str:
    """
    Формирует системный промпт для анализа.
    
    Args:
        order_context: Контекст заказа
        relevant_chunks: Релевантные чанки из RAG
        user_profile: Профиль пользователя (опционально)
        
    Returns:
        str: Системный промпт
    """
    prompt_parts = [
        "Вы - эксперт по анализу планировок помещений и проверке соответствия нормативным требованиям.",
        "Ваша задача - проанализировать предоставленную планировку и выявить риски несоответствия законам и нормам.",
        "",
        "Контекст заказа:",
    ]
    
    if order_context:
        for key, value in order_context.items():
            prompt_parts.append(f"- {key}: {value}")
    else:
        prompt_parts.append("- Контекст не предоставлен")
    
    if user_profile:
        prompt_parts.append("")
        prompt_parts.append("Информация о пользователе:")
        if user_profile.age:
            prompt_parts.append(f"- Возраст: {user_profile.age} лет")
        if user_profile.height:
            prompt_parts.append(f"- Рост: {user_profile.height} см")
        if user_profile.marital_status:
            status_map = {
                "single": "не замужем/не женат",
                "married": "замужем/женат",
                "divorced": "в разводе",
                "widowed": "вдовец/вдова"
            }
            prompt_parts.append(f"- Семейное положение: {status_map.get(user_profile.marital_status, user_profile.marital_status)}")
        if user_profile.profession:
            prompt_parts.append(f"- Профессия: {user_profile.profession}")
        if user_profile.hobbies:
            prompt_parts.append(f"- Увлечения: {', '.join(user_profile.hobbies)}")
        if user_profile.children:
            children_info = ", ".join([f"{child.age} лет" for child in user_profile.children])
            prompt_parts.append(f"- Дети: {len(user_profile.children)} ({children_info})")
    
    prompt_parts.append("")
    prompt_parts.append("Релевантные правила и статьи:")
    if relevant_chunks:
        for i, chunk in enumerate(relevant_chunks, 1):
            prompt_parts.append(f"{i}. {chunk[:300]}...")
    else:
        prompt_parts.append("- Релевантная информация не найдена")
    
    prompt_parts.append("")
    prompt_parts.append(
        "Проанализируйте планировку и верните JSON с полем 'summary' (краткое резюме анализа) "
        "и полем 'risks' (список рисков). Каждый риск должен содержать: "
        "type, description, severity (1-5), zone (опционально), "
        "regulation_reference (опционально), recommendation (опционально), "
        "affected_elements (опционально, список ID), "
        "alts (опционально, массив из 3-5 альтернативных вариантов планировки с геометрией элементов)."
    )
    prompt_parts.append("")
    prompt_parts.append(
        "ВАЖНО: Для каждого риска, если он требует изменения планировки, сгенерируйте в поле 'alts' "
        "от 3 до 5 альтернативных вариантов планировки. Каждый вариант должен содержать геометрию "
        "измененных элементов плана в формате, соответствующем структуре OrderPlanVersion.plan.elements."
    )
    
    return "\n".join(prompt_parts)


def _build_analysis_prompt(
    plan: KanvaPlan,
    plan_description: str,
    relevant_chunks: List[str],
    order_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Формирует промпт для анализа плана.
    
    Args:
        plan: План помещения
        plan_description: Текстовое описание плана
        relevant_chunks: Релевантные чанки из RAG
        order_context: Контекст заказа (может содержать user_request)
        
    Returns:
        str: Промпт для анализа
    """
    prompt_parts = [
        "Проанализируйте следующую планировку помещения:",
        "",
        plan_description,
        ""
    ]
    
    # Если есть запрос пользователя, добавляем его в промпт
    if order_context and "user_request" in order_context:
        prompt_parts.append("ВАЖНО: Пользователь запросил следующие изменения:")
        prompt_parts.append(f"  {order_context['user_request']}")
        prompt_parts.append("")
        prompt_parts.append("При генерации альтернативных вариантов планировки ОБЯЗАТЕЛЬНО учитывайте этот запрос.")
        prompt_parts.append("")
    
    prompt_parts.extend([
        "На основе предоставленных правил и статей определите:",
        "1. Соответствие планировки нормативным требованиям",
        "2. Выявленные риски и их серьезность",
        "3. Рекомендации по устранению рисков",
        "",
        "Для каждого риска, который требует изменения планировки, сгенерируйте в поле 'alts' от 3 до 5 альтернативных вариантов планировки.",
        "Каждый вариант должен содержать геометрию измененных элементов плана в формате, соответствующем структуре OrderPlanVersion.plan.elements.",
        "",
        "Верните результат в формате JSON с полями 'summary' и 'risks'."
    ])
    
    return "\n".join(prompt_parts)


def _get_risk_schema() -> Dict[str, Any]:
    """Возвращает JSON-схему для ответа с рисками."""
    return {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Краткое резюме анализа планировки"
            },
            "risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["TECHNICAL", "LEGAL", "FINANCIAL", "OPERATIONAL"],
                            "description": "Тип риска"
                        },
                        "description": {
                            "type": "string",
                            "description": "Текстовое описание риска",
                            "minLength": 1
                        },
                        "severity": {
                            "type": "integer",
                            "description": "Серьёзность риска по шкале 1–5",
                            "minimum": 1,
                            "maximum": 5
                        },
                        "zone": {
                            "type": "string",
                            "description": "ID элемента на плане (например, wall_12, zone_1)"
                        },
                        "risk_id": {"type": "string"},
                        "severity_str": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"]
                        },
                        "title": {"type": "string"},
                        "regulation_reference": {"type": "string"},
                        "recommendation": {"type": "string"},
                        "affected_elements": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "alternative_suggestion": {"type": "string"},
                        "alts": {
                            "type": "array",
                            "description": "Массив альтернативных вариантов планировки с геометрией (минимум 3, максимум 5)",
                            "minItems": 3,
                            "maxItems": 5,
                            "items": {
                                "type": "object",
                                "description": "Альтернативный вариант планировки с геометрией элементов",
                                "additionalProperties": True,
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "Описание варианта"
                                    },
                                    "elements": {
                                        "type": "array",
                                        "description": "Элементы плана с геометрией",
                                        "items": {
                                            "type": "object",
                                            "additionalProperties": True
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "required": ["type", "description"]
                }
            }
        },
        "required": ["summary", "risks"]
    }


async def analyze_plan(
    plan: KanvaPlan,
    order_context: Dict[str, Any],
    ai_rules: List[Dict[str, Any]],
    articles: List[Dict[str, Any]],
    user_profile: Optional[UserProfile] = None
) -> Tuple[str, List[AiRisk], Optional[Any]]:
    """
    Анализирует план помещения на соответствие законам и возвращает оценку рисков.
    
    Args:
        plan: План помещения в формате KanvaPlan
        order_context: Контекст заказа (словарь с дополнительной информацией)
        ai_rules: Список правил для анализа
        articles: Список статей закона для анализа
        user_profile: Профиль пользователя для персонализации (опционально)
        
    Returns:
        Tuple[str, List[AiRisk], Optional[Any]]: Кортеж из (резюме анализа, список рисков, альтернативы)
    """
    config = load_config()
    model_name = config.gemini_model
    
    try:
        # Форматируем план для анализа
        plan_description = _format_plan_for_analysis(plan)
        
        # Генерируем эмбеддинг для плана
        plan_embedding = await generate_embedding_for_plan(plan)
        
        # Строим RAG индекс из правил и статей
        rag_index = await build_rag_index(ai_rules, articles)
        
        # Получаем релевантные чанки
        relevant_chunks = await retrieve_relevant_chunks(
            plan_embedding,
            rag_index,
            top_k=config.analysis_top_k
        )
        
        # Формируем промпты
        system_prompt = _build_analysis_system_prompt(order_context, relevant_chunks, user_profile)
        analysis_prompt = _build_analysis_prompt(plan, plan_description, relevant_chunks, order_context)
        
        # Генерируем анализ через Gemini API с fallback механизмом
        # Используем лучшие модели с автоматическим переключением при ошибках
        result = await generate_json_with_fallback(
            prompt=analysis_prompt,
            schema=_get_risk_schema(),
            system=system_prompt,
            temperature=config.analysis_temperature,
            top_p=0.8,
        )
        
        summary = result.get("summary", "Анализ завершен.")
        risks_data = result.get("risks", [])
        
        # Парсим риски
        risks: List[AiRisk] = []
        for risk_data in risks_data:
            try:
                normalized_risk = {}
                
                if "type" in risk_data:
                    normalized_risk["type"] = risk_data["type"]
                if "description" in risk_data:
                    normalized_risk["description"] = risk_data["description"]
                
                if "severity" in risk_data:
                    severity = risk_data["severity"]
                    if isinstance(severity, int):
                        normalized_risk["severity"] = severity
                    elif isinstance(severity, str):
                        normalized_risk["severity_str"] = severity
                
                for field in ["zone", "risk_id", "title", "regulation_reference", 
                             "recommendation", "affected_elements", "alternative_suggestion", "severity_str", "alts"]:
                    if field in risk_data:
                        normalized_risk[field] = risk_data[field]
                
                risk = AiRisk(**normalized_risk)
                risks.append(risk)
            except Exception as e:
                # Не логируем полную ошибку, чтобы не раскрывать API ключи
                error_msg = str(e)
                if "API" in error_msg or "key" in error_msg.lower():
                    logger.warning("Ошибка при парсинге риска (детали скрыты для безопасности)")
                else:
                    logger.warning(f"Ошибка при парсинге риска: {error_msg}")
                continue
        
        return summary, risks, None
        
    except Exception as e:
        # Не логируем полную ошибку, чтобы не раскрывать API ключи
        error_msg = str(e)
        if "API" in error_msg or "key" in error_msg.lower() or "403" in error_msg or "PERMISSION_DENIED" in error_msg:
            logger.error("Ошибка при анализе плана (детали скрыты для безопасности)")
        else:
            logger.error(f"Ошибка при анализе плана: {error_msg}")
        return f"Ошибка при анализе: {e}", [], None

