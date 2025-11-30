"""Сервис генерации эмбеддингов."""

from .generator import generate_embedding, chunk_text, generate_embedding_for_plan, generate_embedding_for_user_profile
from .local_embedder import generate_local_embedding

__all__ = [
    "generate_embedding",
    "chunk_text",
    "generate_local_embedding",
    "generate_embedding_for_plan",
    "generate_embedding_for_user_profile",
]

