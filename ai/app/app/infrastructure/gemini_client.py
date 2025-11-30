"""Клиент для работы с Gemini API напрямую через google-genai."""

import asyncio
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from google import genai
from .config import get_gemini_api_key, load_config
from .logging_config import get_logger

# Глобальный экземпляр клиента
_client: Optional[genai.Client] = None


def get_gemini_client() -> genai.Client:
    """
    Получает или создает глобальный экземпляр клиента Gemini API.
    
    Returns:
        genai.Client: Инициализированный клиент Gemini API
        
    Raises:
        ValueError: Если API ключ не найден
    """
    global _client
    
    if _client is None:
        # Проверяем наличие ключа
        get_gemini_api_key()  # Проверка наличия ключа
        _client = genai.Client()  # Берет ключ из env автоматически
    
    return _client


async def generate_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
    tools: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> str:
    """
    Генерирует текст с использованием Gemini API.
    
    Args:
        prompt: Текст запроса
        system: Системный промпт (опционально)
        model: Имя модели (по умолчанию берется из конфигурации .env)
        temperature: Температура генерации (0.0-1.0)
        top_p: Top-p параметр для ядерной выборки
        tools: Список инструментов (function calling) для модели
        **kwargs: Дополнительные параметры
        
    Returns:
        str: Сгенерированный текст
    """
    # Если модель не указана, берем из конфигурации
    if model is None:
        config = load_config()
        model = config.gemini_model
    
    client = get_gemini_client()
    
    # Формируем содержимое
    if system:
        full_prompt = f"{system}\n\n{prompt}"
    else:
        full_prompt = prompt
    
    def _generate():
        # В текущей версии google-genai параметр tools не поддерживается
        # Поэтому просто не передаем его
        # TODO: Обновить когда API будет поддерживать tools
        
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
        )
        return response.text
    
    try:
        response_text = await asyncio.to_thread(_generate)
        return response_text
    except Exception as e:
        # Не раскрываем детали ошибки, чтобы не логировать API ключи
        error_str = str(e)
        # Проверяем, не содержит ли ошибка информацию об API ключе
        if "API" in error_str or "key" in error_str.lower() or "403" in error_str or "PERMISSION_DENIED" in error_str:
            raise RuntimeError("Не удалось получить ответ от Gemini API. Проверьте настройки API ключа.")
        raise RuntimeError(f"Не удалось получить текст из ответа Gemini API: {error_str}")


# Список моделей по убыванию качества для fallback
PLAN_GENERATION_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


async def generate_json(
    prompt: str,
    schema: Dict[str, Any],
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    top_p: float = 0.8,
    **kwargs
) -> Dict[str, Any]:
    """
    Генерирует структурированный JSON с использованием Gemini API.
    
    Args:
        prompt: Текст запроса
        schema: JSON-схема для ответа
        system: Системный промпт (опционально)
        model: Имя модели (по умолчанию берется из конфигурации .env)
        temperature: Температура генерации (0.0-1.0)
        top_p: Top-p параметр для ядерной выборки
        **kwargs: Дополнительные параметры
        
    Returns:
        Dict[str, Any]: Сгенерированный JSON объект
    """
    # Если модель не указана, берем из конфигурации
    if model is None:
        config = load_config()
        model = config.gemini_model
    
    client = get_gemini_client()
    
    # Формируем содержимое
    if system:
        full_prompt = f"{system}\n\n{prompt}"
    else:
        full_prompt = prompt
    
    # Добавляем инструкцию для JSON
    json_prompt = f"{full_prompt}\n\nВерни ответ строго в формате JSON согласно следующей схеме: {json.dumps(schema, ensure_ascii=False)}"
    
    def _generate():
        response = client.models.generate_content(
            model=model,
            contents=json_prompt,
        )
        return response.text
    
    try:
        response_text = await asyncio.to_thread(_generate)
        
        # Пытаемся извлечь JSON из ответа
        response_text = response_text.strip()
        
        # Убираем markdown блоки если есть
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Не удалось распарсить JSON ответ: {e}. Ответ: {response_text[:200]}")
    except Exception as e:
        raise RuntimeError(f"Не удалось получить JSON ответ от Gemini API: {e}")


async def generate_json_with_fallback(
    prompt: str,
    schema: Dict[str, Any],
    system: Optional[str] = None,
    models: Optional[List[str]] = None,
    temperature: float = 0.3,
    top_p: float = 0.8,
    **kwargs
) -> Dict[str, Any]:
    """
    Генерирует структурированный JSON с использованием Gemini API с fallback механизмом.
    При ошибке пытается использовать следующую модель из списка.
    
    Args:
        prompt: Текст запроса
        schema: JSON-схема для ответа
        system: Системный промпт (опционально)
        models: Список моделей для попыток (по умолчанию используется PLAN_GENERATION_MODELS)
        temperature: Температура генерации (0.0-1.0)
        top_p: Top-p параметр для ядерной выборки
        **kwargs: Дополнительные параметры
        
    Returns:
        Dict[str, Any]: Сгенерированный JSON объект
        
    Raises:
        RuntimeError: Если все модели не смогли сгенерировать ответ
    """
    if models is None:
        models = PLAN_GENERATION_MODELS
    
    last_error = None
    
    for model in models:
        try:
            return await generate_json(
                prompt=prompt,
                schema=schema,
                system=system,
                model=model,
                temperature=temperature,
                top_p=top_p,
                **kwargs
            )
        except Exception as e:
            last_error = e
            logger = get_logger("gemini_client")
            logger.warning(f"Ошибка при генерации JSON с моделью {model}: {e}. Пробую следующую модель...")
            continue
    
    # Если все модели не сработали, выбрасываем последнюю ошибку
    raise RuntimeError(
        f"Не удалось сгенерировать JSON ни с одной из моделей ({', '.join(models)}). "
        f"Последняя ошибка: {last_error}"
    )


async def generate_with_vision(
    image_path: str,
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
    top_p: float = 0.8,
    response_schema: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Генерирует ответ с анализом изображения через Vision API.
    
    Args:
        image_path: Путь к изображению
        prompt: Текст запроса
        model: Имя модели (по умолчанию берется из конфигурации .env)
        temperature: Температура генерации (0.0-1.0)
        top_p: Top-p параметр для ядерной выборки
        response_schema: JSON-схема для ответа (опционально)
        **kwargs: Дополнительные параметры
        
    Returns:
        Dict[str, Any]: Ответ модели (может быть JSON, если указан response_schema)
    """
    # Если модель не указана, берем из конфигурации
    if model is None:
        config = load_config()
        model = config.gemini_model
    
    client = get_gemini_client()
    
    # Читаем изображение
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        raise FileNotFoundError(f"Изображение не найдено: {image_path}")
    
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Определяем MIME тип
    mime_type = "image/jpeg"
    if image_path_obj.suffix.lower() == ".png":
        mime_type = "image/png"
    elif image_path_obj.suffix.lower() == ".gif":
        mime_type = "image/gif"
    elif image_path_obj.suffix.lower() == ".webp":
        mime_type = "image/webp"
    
    # Формируем промпт с инструкцией для JSON, если нужно
    if response_schema:
        full_prompt = f"{prompt}\n\nВерни ответ строго в формате JSON согласно следующей схеме: {json.dumps(response_schema, ensure_ascii=False)}"
    else:
        full_prompt = prompt
    
    def _generate():
        from google.genai import types
        
        contents = [
            types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_data)),
            types.Part(text=full_prompt)
        ]
        
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
        return response.text
    
    try:
        response_text = await asyncio.to_thread(_generate)
        
        # Если ожидается JSON, парсим его
        if response_schema:
            response_text = response_text.strip()
            # Убираем markdown блоки если есть
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Не удалось распарсить JSON ответ: {e}. Ответ: {response_text[:200]}")
        
        # Иначе возвращаем как текст в словаре
        return {"text": response_text}
    except Exception as e:
        raise RuntimeError(f"Не удалось получить ответ от Gemini Vision API: {e}")


async def generate_embedding(
    text: str,
    model: str = "models/embedding-001",
    use_fallback: bool = True
) -> List[float]:
    """
    Генерирует эмбеддинг для текста через Gemini API.
    При ошибке автоматически использует локальный fallback.
    
    Args:
        text: Текст для генерации эмбеддинга
        model: Имя модели эмбеддингов (по умолчанию "models/embedding-001")
        use_fallback: Использовать ли локальный fallback при ошибке API
        
    Returns:
        List[float]: Вектор эмбеддинга
    """
    client = get_gemini_client()
    
    def _generate():
        response = client.models.embed_content(
            model=model,
            contents=text,
        )
        return response
    
    try:
        response = await asyncio.to_thread(_generate)
        
        # Извлекаем эмбеддинг
        if response.embeddings and len(response.embeddings) > 0:
            embedding_data = response.embeddings[0]
            if hasattr(embedding_data, "values"):
                return list(embedding_data.values)
            elif hasattr(embedding_data, "embedding"):
                return list(embedding_data.embedding)
            else:
                return list(embedding_data) if isinstance(embedding_data, (list, tuple)) else [float(x) for x in embedding_data]
        
        raise RuntimeError("Не удалось получить эмбеддинг из ответа Gemini API")
    except Exception as e:
        # Если включен fallback и произошла ошибка, используем локальную модель
        if use_fallback:
            try:
                from ..services.embedding.local_embedder import generate_local_embedding
                return await generate_local_embedding(text)
            except ImportError:
                raise RuntimeError(
                    f"Ошибка при генерации эмбеддинга через Gemini API: {e}. "
                    "Для использования локального fallback установите: pip install sentence-transformers"
                ) from e
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Ошибка при генерации эмбеддинга через Gemini API: {e}. "
                    f"Локальный fallback также не сработал: {fallback_error}"
                ) from e
        else:
            raise RuntimeError(f"Ошибка при генерации эмбеддинга: {e}")

