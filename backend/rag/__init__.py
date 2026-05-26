"""RAG package — PDF ingestion and semantic search."""

from rag.chunking import chunk_text
from rag.pdf_loader import extract_text_from_pdf
from rag.vector_store import (
    ingest_pdf,
    search_chunks,
    search_chunks_with_metadata,
    store_embeddings,
)

__all__ = [
    "extract_text_from_pdf",
    "chunk_text",
    "store_embeddings",
    "search_chunks",
    "search_chunks_with_metadata",
    "ingest_pdf",
]
