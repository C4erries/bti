"""Чат-бот для ответов на вопросы пользователя с персонализированными рекомендациями."""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Добавляем путь к моделям
ai_app_path = Path(__file__).parent.parent.parent.parent
if str(ai_app_path) not in sys.path:
    sys.path.insert(0, str(ai_app_path))

from models.chat import ChatMessage, ChatResponse
from models.plan import KanvaPlan
from models.user import UserProfile
from ...infrastructure import generate_text, load_config, get_logger
from ..embedding import generate_embedding, generate_embedding_for_plan, generate_embedding_for_user_profile
from ..rag import retrieve_relevant_chunks, build_rag_index
from ..analysis import analyze_plan
from .tools import get_chat_tools, format_selected_elements_info

logger = get_logger("chat")


def _format_user_profile_for_prompt(user_profile: UserProfile) -> str:
    """
    Форматирует упрощенный профиль пользователя для включения в промпт.
    
    Args:
        user_profile: Профиль пользователя
        
    Returns:
        str: Текстовое представление профиля
    """
    parts = []
    
    if user_profile.age:
        parts.append(f"- Возраст: {user_profile.age} лет")
    
    if user_profile.height:
        parts.append(f"- Рост: {user_profile.height} см")
    
    if user_profile.marital_status:
        status_map = {
            "single": "не замужем/не женат",
            "married": "замужем/женат",
            "divorced": "в разводе",
            "widowed": "вдовец/вдова"
        }
        parts.append(f"- Семейное положение: {status_map.get(user_profile.marital_status, user_profile.marital_status)}")
    
    if user_profile.profession:
        parts.append(f"- Профессия: {user_profile.profession}")
    
    if user_profile.hobbies:
        parts.append(f"- Увлечения: {', '.join(user_profile.hobbies)}")
    
    if user_profile.children:
        children_info = []
        for child in user_profile.children:
            children_info.append(f"{child.age} лет")
        parts.append(f"- Дети: {len(user_profile.children)} ({', '.join(children_info)})")
    
    return "\n".join(parts) if parts else "Профиль пользователя не указан"


def _build_system_prompt(
    plan: Optional[KanvaPlan],
    order_context: Dict[str, Any],
    relevant_chunks: List[str],
    user_profile: Optional[UserProfile] = None,
    risks: Optional[List[Any]] = None
) -> str:
    """
    Формирует системный промпт для чат-бота.
    
    Args:
        plan: План помещения (опционально)
        order_context: Контекст заказа
        relevant_chunks: Релевантные чанки из RAG
        user_profile: Профиль пользователя (опционально)
        risks: Список выявленных рисков (опционально)
        
    Returns:
        str: Системный промпт
    """
    prompt_parts = [
        "Вы - AI-ассистент, помогающий пользователям с вопросами по планировке помещений и нормативным требованиям.",
        "Ваша задача - отвечать на вопросы пользователя, используя предоставленную информацию о правилах и статьях.",
        "Учитывайте профиль пользователя для персонализированных рекомендаций.",
        "Используйте доступные инструменты для выполнения действий, когда это необходимо.",
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
        prompt_parts.append("Информация о пользователе (используйте для персонализированных рекомендаций):")
        prompt_parts.append(_format_user_profile_for_prompt(user_profile))
    
    prompt_parts.append("")
    prompt_parts.append("Релевантная информация из правил и статей:")
    if relevant_chunks:
        for i, chunk in enumerate(relevant_chunks, 1):
            prompt_parts.append(f"{i}. {chunk[:200]}...")
    else:
        prompt_parts.append("- Релевантная информация не найдена")
    
    if plan:
        prompt_parts.append("")
        prompt_parts.append("Информация о текущем плане:")
        prompt_parts.append(f"- Количество элементов: {len(plan.plan.elements)}")
        if plan.plan.objects3d:
            prompt_parts.append(f"- Количество 3D объектов: {len(plan.plan.objects3d)}")
        
        # Добавляем информацию о выделенных элементах
        selected_info = format_selected_elements_info(plan)
        if selected_info:
            prompt_parts.append(selected_info)
        
        # Используем детальное форматирование плана для анализа
        from ..analysis.analyzer import _format_plan_for_analysis
        plan_details = _format_plan_for_analysis(plan)
        prompt_parts.append("")
        prompt_parts.append("Детальная информация о планировке:")
        prompt_parts.append(plan_details)
    
    if risks and len(risks) > 0:
        prompt_parts.append("")
        prompt_parts.append("Выявленные проблемы в планировке:")
        for i, risk in enumerate(risks[:5], 1):
            severity = risk.severity if risk.severity else risk.severity_str or "не указана"
            prompt_parts.append(f"{i}. [{risk.type}] {risk.description} (серьезность: {severity})")
    
    prompt_parts.append("")
    prompt_parts.append("Отвечайте на вопросы пользователя четко и информативно, ссылаясь на релевантные правила и статьи.")
    if user_profile:
        prompt_parts.append("Учитывайте профиль пользователя при даче рекомендаций, чтобы предложения были персонализированными.")
    if plan and plan.selected_elements:
        prompt_parts.append("ОБЯЗАТЕЛЬНО учитывайте выделенные пользователем элементы и работайте с ними в приоритете.")
    
    return "\n".join(prompt_parts)


def _build_prompt_with_history(
    chat_history: List[ChatMessage],
    current_message: ChatMessage
) -> str:
    """
    Формирует промпт с историей сообщений.
    
    Args:
        chat_history: История сообщений
        current_message: Текущее сообщение
        
    Returns:
        str: Промпт с историей
    """
    parts = []
    config = load_config()
    max_history = config.chat_max_history
    
    for hist_msg in chat_history[-max_history:]:
        role_label = "Пользователь" if hist_msg.role == "user" else "Ассистент"
        parts.append(f"{role_label}: {hist_msg.content}")
    
    parts.append(f"Пользователь: {current_message.content}")
    parts.append("Ассистент:")
    
    return "\n".join(parts)


async def process_chat_message(
    message: ChatMessage,
    plan: Optional[KanvaPlan],
    order_context: Dict[str, Any],
    chat_history: List[ChatMessage],
    ai_rules: List[Dict[str, Any]],
    articles: List[Dict[str, Any]],
    user_profile: Optional[UserProfile] = None
) -> ChatResponse:
    """
    Обрабатывает сообщение пользователя и возвращает ответ чат-бота с персонализированными рекомендациями.
    
    Args:
        message: Сообщение пользователя
        plan: План помещения (опционально)
        order_context: Контекст заказа
        chat_history: История сообщений
        ai_rules: Список правил для RAG
        articles: Список статей закона для RAG
        user_profile: Профиль пользователя для персонализации (опционально)
        
    Returns:
        ChatResponse: Ответ чат-бота
    """
    config = load_config()
    model_name = config.gemini_model
    
    try:
        # Генерируем эмбеддинг для запроса пользователя
        query_embedding = await generate_embedding(message.content)
        
        # Строим RAG индекс из правил и статей
        rag_index = await build_rag_index(ai_rules, articles)
        
        # Получаем релевантные чанки
        relevant_chunks = await retrieve_relevant_chunks(
            query_embedding,
            rag_index,
            top_k=config.rag_top_k
        )
        
        # Если есть план, анализируем его для получения рисков
        risks = []
        if plan:
            try:
                summary, risks, _ = await analyze_plan(
                    plan=plan,
                    order_context=order_context,
                    ai_rules=ai_rules,
                    articles=articles,
                    user_profile=user_profile
                )
                logger.info(f"Анализ плана завершен. Выявлено рисков: {len(risks)}")
            except Exception as e:
                logger.warning(f"Не удалось проанализировать план: {e}")
        
        # Формируем промпты
        system_prompt = _build_system_prompt(plan, order_context, relevant_chunks, user_profile, risks)
        full_prompt = _build_prompt_with_history(chat_history, message)
        
        # Получаем инструменты для function calling
        tools = get_chat_tools()
        
        # Генерируем ответ с поддержкой function calling
        response_text = await generate_text(
            prompt=full_prompt,
            system=system_prompt,
            model=model_name,
            temperature=config.chat_temperature,
            top_p=0.9,
            tools=tools,
        )
        
        # Формируем источники из релевантных чанков
        sources = relevant_chunks[:3] if relevant_chunks else None
        
        return ChatResponse(
            content=response_text,
            sources=sources,
            confidence=0.8
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        return ChatResponse(
            content=f"Извините, произошла ошибка при обработке вашего запроса: {e}",
            sources=None,
            confidence=0.0
        )
