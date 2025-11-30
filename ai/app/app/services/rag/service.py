"""RAG (Retrieval Augmented Generation) сервис."""

from typing import List, Dict, Any, Tuple
import numpy as np
from ...infrastructure import load_config
from ..embedding import generate_embedding, chunk_text


class RAGIndex:
    """Индекс для RAG в памяти."""
    
    def __init__(self):
        self.chunks: List[str] = []
        self.embeddings: List[List[float]] = []
        self.metadata: List[Dict[str, Any]] = []
    
    def add_chunk(self, chunk: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """
        Добавляет чанк с эмбеддингом в индекс.
        
        Args:
            chunk: Текстовый чанк
            embedding: Вектор эмбеддинга
            metadata: Метаданные чанка (опционально)
        """
        self.chunks.append(chunk)
        self.embeddings.append(embedding)
        self.metadata.append(metadata or {})
    
    def size(self) -> int:
        """Возвращает количество чанков в индексе."""
        return len(self.chunks)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Вычисляет косинусное сходство между двумя векторами.
    
    Args:
        vec1: Первый вектор
        vec2: Второй вектор
        
    Returns:
        float: Косинусное сходство (от -1 до 1)
    """
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    dot_product = np.dot(vec1_array, vec2_array)
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def _format_rule_text(rule: Dict[str, Any]) -> str:
    """
    Форматирует правило в текстовый формат.
    
    Args:
        rule: Словарь с данными правила
        
    Returns:
        str: Текстовое представление правила
    """
    parts = []
    
    if rule.get("title"):
        parts.append(f"Название правила: {rule['title']}")
    
    if rule.get("description"):
        parts.append(f"Описание: {rule['description']}")
    
    if rule.get("content"):
        parts.append(f"Содержание: {rule['content']}")
    
    if rule.get("regulation_reference"):
        parts.append(f"Ссылка на нормативный документ: {rule['regulation_reference']}")
    
    return "\n".join(parts)


def _format_article_text(article: Dict[str, Any]) -> str:
    """
    Форматирует статью закона в текстовый формат.
    
    Args:
        article: Словарь с данными статьи
        
    Returns:
        str: Текстовое представление статьи
    """
    parts = []
    
    if article.get("title"):
        parts.append(f"Название статьи: {article['title']}")
    
    if article.get("article_number"):
        parts.append(f"Номер статьи: {article['article_number']}")
    
    if article.get("content"):
        parts.append(f"Содержание: {article['content']}")
    
    if article.get("law_name"):
        parts.append(f"Название закона: {article['law_name']}")
    
    if article.get("chapter"):
        parts.append(f"Глава: {article['chapter']}")
    
    return "\n".join(parts)


async def build_rag_index(
    rules: List[Dict[str, Any]],
    articles: List[Dict[str, Any]]
) -> RAGIndex:
    """
    Создает индекс для поиска на основе правил и статей закона.
    
    Args:
        rules: Список правил (словари с полями: title, description, content, regulation_reference и т.д.)
        articles: Список статей закона (словари с полями: title, article_number, content, law_name и т.д.)
        
    Returns:
        RAGIndex: Построенный индекс
    """
    config = load_config()
    index = RAGIndex()
    
    # Добавляем правила в индекс
    for rule in rules:
        rule_text = _format_rule_text(rule)
        chunks = chunk_text(rule_text, chunk_size=config.rag_chunk_size, overlap=config.rag_chunk_overlap)
        
        for chunk in chunks:
            embedding = await generate_embedding(chunk)
            metadata = {
                "type": "rule",
                "rule_id": rule.get("id"),
                "title": rule.get("title"),
                "regulation_reference": rule.get("regulation_reference"),
            }
            index.add_chunk(chunk, embedding, metadata)
    
    # Добавляем статьи закона в индекс
    for article in articles:
        article_text = _format_article_text(article)
        chunks = chunk_text(article_text, chunk_size=config.rag_chunk_size, overlap=config.rag_chunk_overlap)
        
        for chunk in chunks:
            embedding = await generate_embedding(chunk)
            metadata = {
                "type": "article",
                "article_id": article.get("id"),
                "article_number": article.get("article_number"),
                "title": article.get("title"),
                "law_name": article.get("law_name"),
            }
            index.add_chunk(chunk, embedding, metadata)
    
    return index


async def retrieve_relevant_chunks(
    query_embedding: List[float],
    rag_index: RAGIndex,
    top_k: int = 5
) -> List[str]:
    """
    Находит наиболее релевантные чанки на основе эмбеддинга запроса.
    
    Args:
        query_embedding: Вектор эмбеддинга запроса
        rag_index: Индекс RAG
        top_k: Количество наиболее релевантных чанков для возврата
        
    Returns:
        List[str]: Список наиболее релевантных чанков
    """
    if rag_index.size() == 0:
        return []
    
    similarities: List[Tuple[float, int]] = []
    for i, embedding in enumerate(rag_index.embeddings):
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((similarity, i))
    
    # Сортируем по убыванию схожести
    similarities.sort(reverse=True, key=lambda x: x[0])
    
    # Берем top_k наиболее релевантных
    top_indices = [idx for _, idx in similarities[:top_k]]
    return [rag_index.chunks[i] for i in top_indices]

