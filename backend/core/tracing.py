"""
Optional LangSmith / LangChain tracing setup.
"""

import os

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("api")


def setup_langsmith_tracing() -> None:
    """Enable LangSmith when configured via environment variables."""
    if not settings.langchain_tracing:
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"

    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key

    if settings.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    logger.info(
        "LangSmith tracing enabled (project=%s)",
        settings.langchain_project or "default",
    )
