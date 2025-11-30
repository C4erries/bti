"""Локальный генератор эмбеддингов через sentence-transformers."""

from typing import List, Optional, Dict, Any
import asyncio


class LocalEmbedder:
    """
    Класс для генерации локальных эмбеддингов через sentence-transformers.
    Использует кэширование моделей для избежания повторной загрузки.
    """
    
    _instance: Optional['LocalEmbedder'] = None
    
    def __new__(cls):
        """Singleton паттерн - возвращает один экземпляр класса."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models: Dict[str, Any] = {}
        return cls._instance
    
    def _get_model(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Получает или загружает локальную модель для эмбеддингов.
        
        Args:
            model_name: Имя модели из sentence-transformers
            
        Returns:
            Модель sentence-transformers
        """
        # Если модель уже загружена, возвращаем её
        if model_name in self._models:
            return self._models[model_name]
        
        # Загружаем новую модель
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name)
            self._models[model_name] = model
            return model
        except ImportError:
            raise ImportError(
                "Для использования локальных эмбеддингов необходимо установить sentence-transformers: "
                "pip install sentence-transformers"
            )
    
    async def generate_embedding(
        self,
        text: str,
        model_name: str = "all-MiniLM-L6-v2"
    ) -> List[float]:
        """
        Генерирует эмбеддинг используя локальную модель sentence-transformers.
        
        Args:
            text: Текст для генерации эмбеддинга
            model_name: Имя модели (по умолчанию "all-MiniLM-L6-v2" - легкая и быстрая)
            
        Returns:
            List[float]: Вектор эмбеддинга
            
        Raises:
            ValueError: Если текст пустой
            ImportError: Если sentence-transformers не установлен
        """
        if not text:
            raise ValueError("Текст для генерации эмбеддинга не может быть пустым")
        
        # Загружаем модель (синхронно, но в отдельном потоке)
        def _load_and_encode():
            model = self._get_model(model_name)
            # Генерируем эмбеддинг
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        
        # Выполняем в отдельном потоке, чтобы не блокировать event loop
        embedding = await asyncio.to_thread(_load_and_encode)
        return embedding


# Глобальный экземпляр для удобства использования
_embedder = LocalEmbedder()


async def generate_local_embedding(
    text: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> List[float]:
    """
    Генерирует эмбеддинг используя локальную модель sentence-transformers.
    Удобная функция-обёртка над LocalEmbedder.
    
    Args:
        text: Текст для генерации эмбеддинга
        model_name: Имя модели (по умолчанию "all-MiniLM-L6-v2" - легкая и быстрая)
        
    Returns:
        List[float]: Вектор эмбеддинга
        
    Raises:
        ValueError: Если текст пустой
        ImportError: Если sentence-transformers не установлен
    """
    return await _embedder.generate_embedding(text, model_name)

