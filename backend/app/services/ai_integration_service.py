"""Интеграционный сервис для подключения AI модулей из директории ai/."""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid
from dotenv import load_dotenv

# Добавляем путь к AI модулям
project_root = Path(__file__).parent.parent.parent.parent
ai_app_path = project_root / "ai" / "app"
if str(ai_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_path))

# Загружаем переменные окружения из ai/app/.env если существует
ai_env_path = ai_app_path / ".env"
if ai_env_path.exists():
    load_dotenv(ai_env_path)

from app.core.config import settings

# Импорты AI модулей (с обработкой ошибок)
AI_MODULES_AVAILABLE = False
analyze_plan = None
process_chat_message = None

try:
    # Пробуем импортировать через динамический импорт
    import importlib.util
    import sys
    
    # Добавляем путь к AI модулям в sys.path если еще не добавлен
    if str(ai_app_path) not in sys.path:
        sys.path.insert(0, str(ai_app_path))
    
    # Импортируем модули (только Gemini AI - анализ и чат)
    # Добавляем ai/app/app в путь для корректных абсолютных импортов
    ai_app_app_path = ai_app_path / "app"
    if str(ai_app_app_path) not in sys.path:
        sys.path.insert(0, str(ai_app_app_path))
    
    # Импортируем анализ
    try:
        from app.services.analysis.analyzer import analyze_plan
    except ImportError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not import analyze_plan: {e}")
        analyze_plan = None
    
    # Импортируем чат
    try:
        from app.services.chat.chatbot import process_chat_message
    except ImportError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not import process_chat_message: {e}")
        process_chat_message = None
    
    # Импортируем модели
    models_path = ai_app_path / "models"
    if models_path.exists():
        sys.path.insert(0, str(ai_app_path))
        try:
            from models.plan import KanvaPlan
            from models.chat import ChatMessage as AIChatMessage
            from models.user import UserProfile
        except ImportError:
            pass
    
    AI_MODULES_AVAILABLE = (analyze_plan is not None or 
                            process_chat_message is not None)
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"AI modules not available: {e}")
    AI_MODULES_AVAILABLE = False


async def analyze_plan_with_ai(
    plan_data: Dict[str, Any],
    order_context: Dict[str, Any],
    ai_rules: List[Dict[str, Any]],
    articles: List[Dict[str, Any]],
    user_profile: Optional[Dict[str, Any]] = None
) -> tuple[str, List[Dict[str, Any]], Optional[Any]]:
    """
    Анализ плана через AI.
    
    Args:
        plan_data: Данные плана в формате PlanGeometry
        order_context: Контекст заказа
        ai_rules: Список правил AI
        articles: Список статей закона
        user_profile: Профиль пользователя (опционально)
        
    Returns:
        Tuple из (summary, risks, alternatives)
    """
    if not AI_MODULES_AVAILABLE or not analyze_plan:
        return "AI analysis not available", [], None
    
    # Переменные окружения уже загружены при импорте модуля из ai/app/.env
    # Устанавливаем переменные из backend настроек (если не установлены)
    if not os.getenv("GEMINI_API_KEY") and settings.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
    
    # Конвертируем план в формат AI
    kanva_plan = _convert_backend_plan_to_ai_format(plan_data)
    
    # Конвертируем профиль пользователя
    ai_user_profile = None
    if user_profile:
        try:
            ai_user_profile = UserProfile(**user_profile)
        except Exception:
            pass
    
    # Выполняем анализ
    summary, risks, alternatives = await analyze_plan(
        plan=kanva_plan,
        order_context=order_context,
        ai_rules=ai_rules,
        articles=articles,
        user_profile=ai_user_profile
    )
    
    # Конвертируем риски в формат для backend
    risks_dict = [risk.model_dump() if hasattr(risk, 'model_dump') else risk for risk in risks]
    
    return summary, risks_dict, alternatives


async def process_chat_with_ai(
    message: str,
    plan_data: Optional[Dict[str, Any]] = None,
    order_context: Optional[Dict[str, Any]] = None,
    chat_history: List[Dict[str, str]] = None,
    ai_rules: List[Dict[str, Any]] = None,
    articles: List[Dict[str, Any]] = None,
    user_profile: Optional[Dict[str, Any]] = None
) -> str:
    """
    Обработка сообщения чата через AI.
    
    Args:
        message: Текст сообщения
        plan_data: Данные плана (опционально)
        order_context: Контекст заказа
        chat_history: История чата
        ai_rules: Список правил AI
        articles: Список статей закона
        user_profile: Профиль пользователя
        
    Returns:
        Ответ AI в виде текста
    """
    if not AI_MODULES_AVAILABLE or not process_chat_message:
        return "AI chat not available"
    
    # Переменные окружения уже загружены при импорте модуля из ai/app/.env
    # Устанавливаем переменные из backend настроек (если не установлены)
    if not os.getenv("GEMINI_API_KEY") and settings.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
    
    # Создаем сообщение
    ai_message = AIChatMessage(role="user", content=message)
    
    # Конвертируем план
    kanva_plan = None
    if plan_data:
        kanva_plan = _convert_backend_plan_to_ai_format(plan_data)
    
    # Конвертируем историю чата
    ai_history = []
    if chat_history:
        for msg in chat_history:
            ai_history.append(AIChatMessage(
                role=msg.get("role", "user"),
                content=msg.get("content", "")
            ))
    
    # Конвертируем профиль пользователя
    ai_user_profile = None
    if user_profile:
        try:
            ai_user_profile = UserProfile(**user_profile)
        except Exception:
            pass
    
    # Обрабатываем сообщение
    response = await process_chat_message(
        message=ai_message,
        plan=kanva_plan,
        order_context=order_context or {},
        chat_history=ai_history,
        ai_rules=ai_rules or [],
        articles=articles or [],
        user_profile=ai_user_profile
    )
    
    return response.content if hasattr(response, 'content') else str(response)


def _convert_ai_plan_to_backend_format(ai_plan: Any) -> Dict[str, Any]:
    """Конвертация плана из формата AI в формат backend."""
    if hasattr(ai_plan, 'model_dump'):
        return ai_plan.model_dump()
    elif hasattr(ai_plan, 'dict'):
        return ai_plan.dict()
    else:
        return dict(ai_plan)


def _convert_backend_plan_to_ai_format(plan_data: Dict[str, Any]) -> Any:
    """Конвертация плана из формата backend в формат AI."""
    if not AI_MODULES_AVAILABLE:
        return None
    
    try:
        # Создаем KanvaPlan из данных backend
        # KanvaPlan ожидает OrderPlanVersion, но мы можем создать его из plan_data
        from models.plan import OrderPlanVersion, Plan, PlanMeta
        
        # Если plan_data уже содержит структуру OrderPlanVersion
        if "plan" in plan_data:
            return KanvaPlan(**plan_data)
        else:
            # Создаем OrderPlanVersion из plan_data
            order_plan_version = OrderPlanVersion(
                id=str(uuid.uuid4()),
                orderId=str(uuid.uuid4()),
                versionType="ORIGINAL",
                plan=Plan(**plan_data),
                createdAt=None
            )
            return KanvaPlan(
                id=order_plan_version.id,
                orderId=order_plan_version.orderId,
                versionType=order_plan_version.versionType,
                plan=order_plan_version.plan,
                createdAt=order_plan_version.createdAt
            )
    except Exception as e:
        print(f"Error converting plan format: {e}")
        return None

