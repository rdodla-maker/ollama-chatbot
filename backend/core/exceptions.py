"""Custom exceptions and helpers for API error responses."""


class OllamaConnectionError(Exception):
    """Raised when Ollama is unreachable or returns an error."""


class RAGError(Exception):
    """Raised for PDF / vector store processing failures."""
