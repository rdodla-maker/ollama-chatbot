"""PDF semantic search tool (wraps RAG layer)."""

from core.logging_config import get_logger
from rag.vector_store import search_chunks

logger = get_logger("tools")


def pdf_search_tool(query: str) -> str:
    try:
        results = search_chunks(query)
        if not results:
            return "No relevant PDF content found. Upload a PDF first."
        logger.info("PDF search returned %s chunks", len(results))
        return "\n".join(results)
    except Exception as e:
        logger.warning("PDF search error: %s", e)
        return f"Error: {str(e)}"
