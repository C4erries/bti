"""Генерация эмбеддингов и разбиение текста на чанки."""

from typing import List, Optional
import sys
from pathlib import Path

# Настраиваем пути для абсолютных импортов
ai_app_path = Path(__file__).parent.parent.parent.parent
if str(ai_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_path))

from app.infrastructure import load_config
import sys
from pathlib import Path

# Добавляем путь к моделям
ai_app_path = Path(__file__).parent.parent.parent.parent
if str(ai_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_path))

from models.plan import KanvaPlan, WallGeometry
from models.user import UserProfile
from app.services.embedding.local_embedder import generate_local_embedding


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Разбивает длинный текст на более мелкие чанки с перекрытием.
    
    Args:
        text: Текст для разбиения
        chunk_size: Размер чанка в символах
        overlap: Перекрытие между чанками в символах
        
    Returns:
        List[str]: Список чанков текста
    """
    if not text:
        return []
    
    chunks: List[str] = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start >= text_length:
            break
    
    return chunks


async def generate_embedding(
    text: str,
    model_name: Optional[str] = None
) -> List[float]:
    """
    Генерирует векторный эмбеддинг для текста используя локальную модель sentence-transformers.
    
    Args:
        text: Текст для генерации эмбеддинга
        model_name: Имя модели sentence-transformers (опционально, по умолчанию берется из конфигурации)
        
    Returns:
        List[float]: Вектор эмбеддинга
        
    Raises:
        ValueError: Если текст пустой
    """
    if not text:
        raise ValueError("Текст для генерации эмбеддинга не может быть пустым")
    
    config = load_config()
    
    # Используем указанную модель или модель из конфигурации
    if model_name is None:
        model_name = config.local_embedding_model
    
    return await generate_local_embedding(text, model_name=model_name)


def _format_plan_for_embedding(plan: KanvaPlan) -> str:
    """
    Форматирует план в текстовый формат для генерации эмбеддинга.
    
    Args:
        plan: План помещения (OrderPlanVersion)
        
    Returns:
        str: Текстовое представление плана
    """
    parts = []
    plan_data = plan.plan
    
    # Метаданные
    if plan_data.meta.scale:
        parts.append(f"Масштаб плана: {plan_data.meta.scale.px_per_meter} px/м")
    parts.append(f"Размеры: {plan_data.meta.width}×{plan_data.meta.height} {plan_data.meta.unit}")
    if plan_data.meta.ceiling_height_m:
        parts.append(f"Высота потолка: {plan_data.meta.ceiling_height_m} м")
    
    # Элементы
    walls = [e for e in plan_data.elements if e.type == "wall"]
    zones = [e for e in plan_data.elements if e.type == "zone"]
    labels = [e for e in plan_data.elements if e.type == "label"]
    
    # Подсчитываем проёмы
    openings_count = 0
    for wall in walls:
        if isinstance(wall.geometry, WallGeometry) and wall.geometry.openings:
            openings_count += len(wall.geometry.openings)
    
    parts.append(f"Элементы: {len(walls)} стен, {len(zones)} зон, {len(labels)} меток, {openings_count} проёмов")
    
    # Зоны
    if zones:
        parts.append("Зоны:")
        for zone in zones:
            zone_info = f"  - Зона {zone.id}"
            if zone.zoneType:
                zone_info += f" (тип: {zone.zoneType}"
            if zone.role:
                zone_info += f", роль: {zone.role}"
            zone_info += ")"
            parts.append(zone_info)
    
    # 3D объекты
    if plan_data.objects3d:
        parts.append(f"3D объекты: {len(plan_data.objects3d)}")
        obj_types = {}
        for obj3d in plan_data.objects3d:
            obj_types[obj3d.type] = obj_types.get(obj3d.type, 0) + 1
        for obj_type, count in obj_types.items():
            parts.append(f"  - {obj_type}: {count}")
    
    return "\n".join(parts)


async def generate_embedding_for_plan(plan: KanvaPlan) -> List[float]:
    """
    Генерирует эмбеддинг для плана помещения.
    
    Args:
        plan: План помещения
        
    Returns:
        List[float]: Вектор эмбеддинга плана
    """
    plan_text = _format_plan_for_embedding(plan)
    return await generate_embedding(plan_text)


def _format_user_profile_for_embedding(user_profile: UserProfile) -> str:
    """
    Форматирует упрощенный профиль пользователя в текстовый формат для генерации эмбеддинга.
    
    Args:
        user_profile: Профиль пользователя
        
    Returns:
        str: Текстовое представление профиля
    """
    parts = []
    
    if user_profile.age:
        parts.append(f"Возраст: {user_profile.age} лет")
    
    if user_profile.height:
        parts.append(f"Рост: {user_profile.height} см")
    
    if user_profile.marital_status:
        status_map = {
            "single": "не замужем/не женат",
            "married": "замужем/женат",
            "divorced": "в разводе",
            "widowed": "вдовец/вдова"
        }
        parts.append(f"Семейное положение: {status_map.get(user_profile.marital_status, user_profile.marital_status)}")
    
    if user_profile.profession:
        parts.append(f"Профессия: {user_profile.profession}")
    
    if user_profile.hobbies:
        parts.append(f"Увлечения: {', '.join(user_profile.hobbies)}")
    
    if user_profile.children:
        children_info = ", ".join([f"{child.age} лет" for child in user_profile.children])
        parts.append(f"Дети: {len(user_profile.children)} ({children_info})")
    
    return "\n".join(parts) if parts else "Профиль пользователя не указан"


async def generate_embedding_for_user_profile(user_profile: UserProfile) -> List[float]:
    """
    Генерирует эмбеддинг для профиля пользователя.
    
    Args:
        user_profile: Профиль пользователя
        
    Returns:
        List[float]: Вектор эмбеддинга профиля
    """
    profile_text = _format_user_profile_for_embedding(user_profile)
    return await generate_embedding(profile_text)

