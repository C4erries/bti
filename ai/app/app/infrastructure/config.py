"""Настройки и загрузка конфигурации из переменных окружения."""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Загружаем переменные окружения из _env файла (или .env для обратной совместимости)
from pathlib import Path
_env_path = Path(__file__).parent.parent.parent / "_env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Fallback на .env для обратной совместимости
    load_dotenv()


class AppConfig(BaseModel):
    """Типизированная конфигурация приложения."""
    
    gemini_api_key: Optional[str] = Field(None, description="API ключ Gemini")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Модель Gemini")
    local_embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Модель для локальных эмбеддингов (sentence-transformers)"
    )
    
    # Настройки RAG
    rag_chunk_size: int = Field(default=1000, description="Размер чанка для RAG")
    rag_chunk_overlap: int = Field(default=200, description="Перекрытие чанков для RAG")
    rag_top_k: int = Field(default=5, description="Количество релевантных чанков для RAG")
    
    # Настройки чата
    chat_temperature: float = Field(default=0.7, description="Температура для генерации чата")
    chat_max_history: int = Field(default=10, description="Максимальное количество сообщений в истории")
    
    # Настройки анализа
    analysis_temperature: float = Field(default=0.3, description="Температура для анализа")
    analysis_top_k: int = Field(default=10, description="Количество релевантных чанков для анализа")
    
    # Настройки API CubiCasa5K
    cubicasa_api_url: str = Field(
        default="http://localhost:8000",
        description="URL API CubiCasa5K для обработки изображений планировок"
    )
    cubicasa_timeout: float = Field(
        default=300.0,
        description="Таймаут запроса к API CubiCasa5K в секундах"
    )


_config_instance: Optional[AppConfig] = None


def load_config() -> AppConfig:
    """
    Загружает и возвращает типизированную конфигурацию из переменных окружения.
    
    Returns:
        AppConfig: Конфигурация приложения
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = AppConfig(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            local_embedding_model=os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            rag_chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            rag_chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
            rag_top_k=int(os.getenv("RAG_TOP_K", "5")),
            chat_temperature=float(os.getenv("CHAT_TEMPERATURE", "0.7")),
            chat_max_history=int(os.getenv("CHAT_MAX_HISTORY", "10")),
            analysis_temperature=float(os.getenv("ANALYSIS_TEMPERATURE", "0.3")),
            analysis_top_k=int(os.getenv("ANALYSIS_TOP_K", "10")),
            cubicasa_api_url=os.getenv("CUBICASA_API_URL", "http://localhost:8000"),
            cubicasa_timeout=float(os.getenv("CUBICASA_TIMEOUT", "300.0")),
        )
    
    return _config_instance


def get_gemini_api_key() -> str:
    """
    Получает API ключ Gemini из переменных окружения.
    
    Returns:
        str: API ключ
        
    Raises:
        ValueError: Если API ключ не найден
    """
    config = load_config()
    api_key = config.gemini_api_key
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY не найден в переменных окружения. "
            "Убедитесь, что файл _env (или .env) существует и содержит GEMINI_API_KEY."
        )
    
    return api_key

