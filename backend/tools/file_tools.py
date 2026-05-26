"""
Secure file reader and folder scanner tools.
"""

import os
from pathlib import Path

from core.config import settings
from core.logging_config import get_logger
from core.security import (
    IGNORED_DIR_NAMES,
    is_ignored_dir,
    is_likely_binary,
    read_text_file_limited,
    resolve_safe_path,
)

logger = get_logger("tools")


def file_reader_tool(file_path: str) -> str:
    """Read a text file inside the allowed project root."""
    try:
        safe_path = resolve_safe_path(file_path)

        if not safe_path.is_file():
            return f"Error reading file: not a file: {safe_path}"

        if is_likely_binary(safe_path):
            return f"Error reading file: binary or unsupported file: {safe_path.name}"

        content = read_text_file_limited(safe_path)
        logger.info("Read file: %s (%s chars)", safe_path, len(content))
        return content

    except Exception as e:
        logger.warning("File read failed: %s", e)
        return f"Error reading file: {str(e)}"


def folder_scanner_tool(folder_path: str) -> str:
    """List files under a folder inside the allowed root, skipping ignored dirs."""
    try:
        safe_path = resolve_safe_path(folder_path)

        if not safe_path.is_dir():
            return f"Error scanning folder: not a directory: {safe_path}"

        files_data: list[str] = []

        for root, dirs, files in os.walk(safe_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if not is_ignored_dir(d)]

            for file in files:
                full_path = Path(root) / file
                if is_likely_binary(full_path):
                    continue
                files_data.append(str(full_path.resolve()))

        logger.info(
            "Scanned folder %s — %s files listed", safe_path, len(files_data)
        )
        return "\n".join(files_data) if files_data else "No readable files found."

    except Exception as e:
        logger.warning("Folder scan failed: %s", e)
        return f"Error scanning folder: {str(e)}"
