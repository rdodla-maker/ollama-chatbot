"""Deprecated codebase index stub.

Original indexing logic has been archived to `backend/archived/rag`.
This module provides minimal stub functions to preserve API compatibility
without performing heavy indexing work.
"""

from core.logging_config import get_logger

logger = get_logger("rag.codebase")


def index_codebase() -> dict:
    logger.info("index_codebase called but is archived/disabled")
    return {"files": 0, "chunks": 0, "message": "Codebase indexing is archived/disabled."}


def search_codebase(query: str, n_results: int = 5) -> list:
    logger.info("search_codebase called but is archived/disabled")
    return []
