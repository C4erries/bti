"""Интеграционный сервис для подключения AI модулей из директории ai/."""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid

# Добавляем путь к AI модулям
project_root = Path(__file__).parent.parent.parent.parent
ai_app_path = project_root / "ai" / "app"
if str(ai_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_path))

from app.core.config import settings

# Импорты AI модулей (с обработкой ошибок)
try:
    # Пробуем импортировать из ai/app/app/services
    from app.services.plan_processing import process_plan_from_image, CubiCasaProcessingError
    from app.services.analysis import analyze_plan
    from app.services.chat import process_chat_message
    from models.plan import OrderPlanVersion as AIOrderPlanVersion, KanvaPlan
    from models.chat import ChatMessage as AIChatMessage, ChatResponse as AIChatResponse
    from models.risks import AiRisk
    from models.user import UserProfile
    AI_MODULES_AVAILABLE = True
except ImportError:
    try:
        # Альтернативный путь импорта
        import importlib.util
        plan_processing_path = ai_app_path / "app" / "services" / "plan_processing" / "__init__.py"
        if plan_processing_path.exists():
            spec = importlib.util.spec_from_file_location("plan_processing", plan_processing_path)
            plan_processing = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plan_processing)
            process_plan_from_image = plan_processing.process_plan_from_image
            CubiCasaProcessingError = plan_processing.CubiCasaProcessingError
        else:
            process_plan_from_image = None
            CubiCasaProcessingError = Exception
        
        analysis_path = ai_app_path / "app" / "services" / "analysis" / "__init__.py"
        if analysis_path.exists():
            spec = importlib.util.spec_from_file_location("analysis", analysis_path)
            analysis = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(analysis)
            analyze_plan = analysis.analyze_plan
        else:
            analyze_plan = None
        
        chat_path = ai_app_path / "app" / "services" / "chat" / "__init__.py"
        if chat_path.exists():
            spec = importlib.util.spec_from_file_location("chat", chat_path)
            chat = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(chat)
            process_chat_message = chat.process_chat_message
        else:
            process_chat_message = None
        
        AI_MODULES_AVAILABLE = (process_plan_from_image is not None or 
                                analyze_plan is not None or 
                                process_chat_message is not None)
    except Exception as e:
        print(f"Warning: AI modules not available: {e}")
        AI_MODULES_AVAILABLE = False
        process_plan_from_image = None
        analyze_plan = None
        process_chat_message = None
        CubiCasaProcessingError = Exception


async def process_plan_image(
    image_bytes: bytes,
    order_id: Optional[uuid.UUID] = None,
    version_type: str = "ORIGINAL",
    px_per_meter: Optional[float] = None
) -> Dict[str, Any]:
    """
    Обработка изображения плана через CubiCasa API.
    
    Args:
        image_bytes: Байты изображения
        order_id: ID заказа
        version_type: Тип версии
        px_per_meter: Пикселей на метр
        
    Returns:
        Dict с результатом обработки в формате OrderPlanVersion
        
    Raises:
        CubiCasaProcessingError: При ошибке обработки
    """
    if not AI_MODULES_AVAILABLE or not process_plan_from_image:
        raise RuntimeError("AI modules not available")
    
    # Устанавливаем переменные окружения для AI модулей
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key or "")
    os.environ.setdefault("CUBICASA_API_URL", settings.cubicasa_api_url)
    os.environ.setdefault("CUBICASA_TIMEOUT", str(settings.cubicasa_timeout))
    
    order_id_str = str(order_id) if order_id else None
    result = await process_plan_from_image(
        image_bytes=image_bytes,
        order_id=order_id_str,
        version_type=version_type,
        px_per_meter=px_per_meter,
        cubicasa_api_url=settings.cubicasa_api_url
    )
    
    # Конвертируем в формат для backend
    return _convert_ai_plan_to_backend_format(result)


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
    
    # Устанавливаем переменные окружения
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key or "")
    
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
    
    # Устанавливаем переменные окружения
    os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key or "")
    
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

