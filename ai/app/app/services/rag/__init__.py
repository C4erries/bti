"""RAG (Retrieval Augmented Generation) сервис."""

from .service import RAGIndex, build_rag_index, retrieve_relevant_chunks, cosine_similarity

__all__ = [
    "RAGIndex",
    "build_rag_index",
    "retrieve_relevant_chunks",
    "cosine_similarity",
]

