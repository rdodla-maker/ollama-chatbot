"""Shared embedding model for RAG and memory."""

from sentence_transformers import SentenceTransformer

from core.logging_config import get_logger

logger = get_logger("rag")

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model
