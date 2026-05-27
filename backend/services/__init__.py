"""External service clients."""

from services.ollama_service import generate_completion, stream_completion
from services.application_service import generate_application_materials

__all__ = ["generate_completion", "stream_completion", "generate_application_materials"]
