"""Репозиторий для работы с RAG chunks в базе данных."""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models.db_models import RAGChunk


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Вычисляет косинусное сходство между двумя векторами.
    
    Args:
        vec1: Первый вектор
        vec2: Второй вектор
        
    Returns:
        float: Косинусное сходство (от -1 до 1)
    """
    import numpy as np
    
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    dot_product = np.dot(vec1_array, vec2_array)
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


class RAGRepository:
    """Репозиторий для работы с RAG chunks."""

    def __init__(self, session: AsyncSession):
        """
        Инициализирует репозиторий.
        
        Args:
            session: Асинхронная сессия БД
        """
        self.session = session

    async def add_chunk(
        self,
        source_type: str,
        source_id: uuid.UUID,
        chunk_index: int,
        text: str,
        embedding: List[float],
        order_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> RAGChunk:
        """
        Добавляет чанк в БД.
        
        Args:
            source_type: Тип источника (article, order_file, ai_rule)
            source_id: ID источника
            chunk_index: Индекс чанка в источнике
            text: Текст чанка
            embedding: Вектор эмбеддинга
            order_id: ID заказа (опционально)
            meta: Метаданные (опционально)
            
        Returns:
            RAGChunk: Созданный чанк
        """
        chunk = RAGChunk(
            id=uuid.uuid4(),
            source_type=source_type,
            source_id=source_id,
            order_id=order_id,
            chunk_index=chunk_index,
            text=text,
            embedding=embedding,
            meta=meta
        )
        self.session.add(chunk)
        await self.session.flush()
        return chunk

    async def get_chunks_by_source(
        self,
        source_type: str,
        source_id: uuid.UUID
    ) -> List[RAGChunk]:
        """
        Получает все чанки для указанного источника.
        
        Args:
            source_type: Тип источника
            source_id: ID источника
            
        Returns:
            List[RAGChunk]: Список чанков
        """
        stmt = select(RAGChunk).where(
            RAGChunk.source_type == source_type,
            RAGChunk.source_id == source_id
        ).order_by(RAGChunk.chunk_index)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_chunks_by_order(
        self,
        order_id: uuid.UUID
    ) -> List[RAGChunk]:
        """
        Получает все чанки для указанного заказа.
        
        Args:
            order_id: ID заказа
            
        Returns:
            List[RAGChunk]: Список чанков
        """
        stmt = select(RAGChunk).where(
            RAGChunk.order_id == order_id
        ).order_by(RAGChunk.chunk_index)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_type: Optional[str] = None,
        order_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Находит наиболее похожие чанки на основе косинусного сходства.
        
        Args:
            query_embedding: Вектор эмбеддинга запроса
            top_k: Количество наиболее похожих чанков
            source_type: Фильтр по типу источника (опционально)
            order_id: Фильтр по ID заказа (опционально)
            
        Returns:
            List[Dict[str, Any]]: Список словарей с чанками и их схожестью
        """
        # Получаем все чанки (или фильтрованные)
        conditions = []
        if source_type:
            conditions.append(RAGChunk.source_type == source_type)
        if order_id:
            conditions.append(RAGChunk.order_id == order_id)
        
        if conditions:
            stmt = select(RAGChunk).where(*conditions)
        else:
            stmt = select(RAGChunk)
        
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())
        
        if not chunks:
            return []
        
        # Вычисляем схожесть для каждого чанка
        similarities = []
        for chunk in chunks:
            similarity = cosine_similarity(query_embedding, chunk.embedding)
            similarities.append({
                "chunk": chunk,
                "similarity": similarity,
                "text": chunk.text,
                "metadata": chunk.meta or {}
            })
        
        # Сортируем по убыванию схожести
        similarities.sort(reverse=True, key=lambda x: x["similarity"])
        
        # Возвращаем top_k
        return similarities[:top_k]

    async def delete_chunks_by_source(
        self,
        source_type: str,
        source_id: uuid.UUID
    ) -> int:
        """
        Удаляет все чанки для указанного источника.
        
        Args:
            source_type: Тип источника
            source_id: ID источника
            
        Returns:
            int: Количество удаленных чанков
        """
        stmt = select(RAGChunk).where(
            RAGChunk.source_type == source_type,
            RAGChunk.source_id == source_id
        )
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())
        
        count = len(chunks)
        for chunk in chunks:
            await self.session.delete(chunk)
        
        return count

    async def count_chunks(self) -> int:
        """
        Возвращает общее количество чанков в БД.
        
        Returns:
            int: Количество чанков
        """
        stmt = select(func.count(RAGChunk.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

