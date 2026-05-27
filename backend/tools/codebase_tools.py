"""Deprecated codebase tools stub.

Original implementations moved to `backend/archived/tools` and
`backend/archived/rag`. These stubs preserve public API but return
informative messages so the codebase remains runnable.
"""

from core.logging_config import get_logger

logger = get_logger("tools.codebase")


def codebase_search_tool(query: str) -> str:
    logger.info("codebase_search_tool called but is archived")
    return (
        "Codebase search has been archived/disabled. "
        "Restore from backend/archived if needed."
    )


def analyze_repository_tool(_query: str = "") -> str:
    logger.info("analyze_repository_tool called but is archived")
    return (
        "Repository analysis is archived/disabled. "
        "Restore from backend/archived if needed."
    )
