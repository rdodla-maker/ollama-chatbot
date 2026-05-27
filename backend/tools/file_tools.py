"""Deprecated file tools stub.

Original implementations moved to `backend/archived/tools`.
These stubs preserve the public API surface but return informative messages
so the project remains runnable while removing learning/demo features.
"""

from core.logging_config import get_logger

logger = get_logger("tools.file_tools")


def file_reader_tool(file_path: str) -> str:
    logger.info("file_reader_tool called but is archived")
    return (
        "File reader tool has been archived/removed. "
        "Restore from backend/archived if needed."
    )


def folder_scanner_tool(folder_path: str) -> str:
    logger.info("folder_scanner_tool called but is archived")
    return (
        "Folder scanner tool has been archived/removed. "
        "Restore from backend/archived if needed."
    )
