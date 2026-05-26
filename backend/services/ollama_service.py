"""Async Ollama client using httpx."""

import json
from collections.abc import AsyncIterator

import httpx

from core.config import settings
from core.exceptions import OllamaConnectionError
from core.logging_config import get_logger

logger = get_logger("services")

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def _handle_http_error(exc: Exception) -> None:
    if isinstance(exc, httpx.ConnectError):
        raise OllamaConnectionError(
            "Cannot connect to Ollama. "
            "Ensure Ollama is running (ollama serve) and the model is pulled."
        ) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise OllamaConnectionError("Ollama request timed out.") from exc
    if isinstance(exc, httpx.HTTPStatusError):
        raise OllamaConnectionError(
            f"Ollama returned HTTP {exc.response.status_code}."
        ) from exc
    raise OllamaConnectionError(f"Ollama error: {exc}") from exc


async def generate_completion(prompt: str, stream: bool = False) -> str:
    """Call Ollama /api/generate asynchronously."""
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                settings.ollama_generate_url,
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("response", "")
    except OllamaConnectionError:
        raise
    except Exception as exc:
        logger.error("Ollama generate failed: %s", exc)
        _handle_http_error(exc)
        return ""


async def stream_completion(prompt: str) -> AsyncIterator[str]:
    """Stream tokens from Ollama /api/generate."""
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST",
                settings.ollama_generate_url,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
    except OllamaConnectionError:
        raise
    except Exception as exc:
        logger.error("Ollama stream failed: %s", exc)
        _handle_http_error(exc)
