from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    api_v1_prefix: str = Field(default="/api/v1")
    project_name: str = Field(default="Умное БТИ")
    secret_key: str = Field(default="supersecret")
    access_token_expire_minutes: int = Field(default=60)
    algorithm: str = Field(default="HS256")
    database_url: str = Field(default="sqlite:///./app.db")
    static_root: str = Field(default="static")
    static_dir: str = Field(default="static")
    static_url: str = Field(default="/static")
    request_documents_prefix: str = Field(default="requests")
    
    # AI настройки (только Gemini)
    gemini_api_key: Optional[str] = Field(default=None, description="API ключ Gemini")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Модель Gemini")
    local_embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Модель для локальных эмбеддингов")
    rag_chunk_size: int = Field(default=1000, description="Размер чанка для RAG")
    rag_chunk_overlap: int = Field(default=200, description="Перекрытие чанков для RAG")
    rag_top_k: int = Field(default=5, description="Количество релевантных чанков для RAG")
    chat_temperature: float = Field(default=0.7, description="Температура для генерации чата")
    chat_max_history: int = Field(default=10, description="Максимальное количество сообщений в истории")
    analysis_temperature: float = Field(default=0.3, description="Температура для анализа")
    analysis_top_k: int = Field(default=10, description="Количество релевантных чанков для анализа")

    model_config = {
        "env_file": "_env",  # Используем _env вместо .env для безопасности
        "case_sensitive": False,
        "extra": "ignore",  # Игнорируем неизвестные переменные из _env
    }


settings = Settings()
