"""SQLAlchemy модели для базы данных."""

import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
from ..infrastructure.database import Base


class GUID(TypeDecorator):
    """Универсальный тип для UUID, работает с PostgreSQL и SQLite."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class RAGChunk(Base):
    """Модель для хранения чанков RAG."""
    __tablename__ = "rag_chunks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(50), nullable=False)  # article, order_file, ai_rule
    source_id = Column(GUID(), nullable=False)
    order_id = Column(GUID(), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)  # Храним как JSON массив чисел
    meta = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            "id": str(self.id),
            "source_type": self.source_type,
            "source_id": str(self.source_id),
            "order_id": str(self.order_id) if self.order_id else None,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "embedding": self.embedding,
            "meta": self.meta,
        }


class AIRule(Base):
    """Модель для хранения AI правил."""
    __tablename__ = "ai_rule"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # Может быть Text или JSON
    tags = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "is_active": self.is_active,
        }


class Article(Base):
    """Модель для хранения статей закона."""
    __tablename__ = "articles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
        }


class Order(Base):
    """Минимальная модель для таблицы orders (для поддержки Foreign Key)."""
    __tablename__ = "orders"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)


class AIAnalysis(Base):
    """Модель для хранения результатов AI анализа."""
    __tablename__ = "ai_analysis"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    order_id = Column(GUID(), ForeignKey("orders.id"), nullable=False)
    decision_status = Column(
        String(50),
        nullable=False
    )  # ALLOWED, FORBIDDEN, NEEDS_APPROVAL, UNKNOWN
    summary = Column(Text, nullable=True)
    risks = Column(JSON, nullable=True)  # Список AiRisk объектов

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует модель в словарь."""
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "decision_status": self.decision_status,
            "summary": self.summary,
            "risks": self.risks,
        }

