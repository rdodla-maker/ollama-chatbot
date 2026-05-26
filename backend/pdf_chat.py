"""
Backward-compatible shim for legacy imports.

Prefer: from rag import extract_text_from_pdf, search_chunks, ...
"""

from rag import (
    chunk_text,
    extract_text_from_pdf,
    search_chunks,
    store_embeddings,
)

__all__ = [
    "extract_text_from_pdf",
    "chunk_text",
    "store_embeddings",
    "search_chunks",
]
