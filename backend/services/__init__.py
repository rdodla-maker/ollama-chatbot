"""External service clients."""

from services.ollama_service import generate_completion, stream_completion

__all__ = ["generate_completion", "stream_completion"]
