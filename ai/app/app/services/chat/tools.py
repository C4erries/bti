"""Инструменты (function calling) для чат-бота."""

from typing import List, Dict, Any, Optional
from v2.models.plan import KanvaPlan


def get_chat_tools() -> List[Dict[str, Any]]:
    """
    Возвращает список инструментов (functions) для модели Gemini.
    
    Returns:
        List[Dict[str, Any]]: Список инструментов в формате Gemini Function Calling
    """
    return [
        {
            "name": "generate_plan_alternatives",
            "description": "Генерирует два варианта перепланировки помещения: ближайший к оригиналу и оптимальный с учетом профиля пользователя. Используйте этот инструмент, когда пользователь запрашивает варианты перепланировки, альтернативные планировки или оптимизацию планировки.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Причина запроса вариантов перепланировки"
                    }
                },
                "required": ["reason"]
            }
        },
        {
            "name": "analyze_plan_risks",
            "description": "Анализирует план помещения на наличие рисков и проблем. Используйте этот инструмент, когда пользователь спрашивает о проблемах в планировке, рисках, нарушениях норм или хочет проверить соответствие требованиям.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Области плана, на которые нужно обратить особое внимание (например, конкретные зоны или элементы)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_plan_element_info",
            "description": "Получает детальную информацию о конкретных элементах плана. Используйте этот инструмент, когда пользователь спрашивает о конкретных элементах, зонах, стенах, дверях или окнах на плане.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Список ID элементов, о которых нужно получить информацию"
                    }
                },
                "required": ["element_ids"]
            }
        },
        {
            "name": "search_regulations",
            "description": "Ищет релевантную информацию из правил и статей закона по заданному вопросу. Используйте этот инструмент, когда пользователь спрашивает о нормативных требованиях, правилах, законах или хочет найти конкретную информацию из нормативных документов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос для поиска в правилах и статьях"
                    }
                },
                "required": ["query"]
            }
        }
    ]


def format_selected_elements_info(plan: Optional[KanvaPlan]) -> str:
    """
    Форматирует информацию о выделенных элементах плана.
    
    Args:
        plan: План помещения (OrderPlanVersion)
        
    Returns:
        str: Текстовое представление выделенных элементов
    """
    if not plan or not plan.selected_elements:
        return ""
    
    parts = []
    parts.append("")
    parts.append("ВАЖНО: Пользователь выделил следующие элементы на плане (работайте с ними в приоритете):")
    
    selected_ids = set(plan.selected_elements)
    plan_data = plan.plan
    
    # Выделенные элементы плана
    for element in plan_data.elements:
        if element.id in selected_ids:
            info = f"  - {element.type.upper()}: {element.id}"
            if element.zoneType:
                info += f" (тип зоны: {element.zoneType})"
            if element.role:
                info += f" (роль: {element.role})"
            parts.append(info)
    
    # Выделенные 3D объекты
    if plan_data.objects3d:
        for obj3d in plan_data.objects3d:
            if obj3d.id in selected_ids:
                info = f"  - 3D {obj3d.type.upper()}: {obj3d.id}"
                if obj3d.zoneId:
                    info += f" (зона: {obj3d.zoneId})"
                if obj3d.wallId:
                    info += f" (стена: {obj3d.wallId})"
                parts.append(info)
    
    parts.append("")
    parts.append("При ответе на вопросы пользователя обязательно учитывайте эти выделенные элементы и работайте с ними в первую очередь.")
    
    return "\n".join(parts)

