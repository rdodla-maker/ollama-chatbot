"""
Structured logging setup for API, tools, RAG, and agent modules.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure application-wide logging once at startup."""

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)
    root.addHandler(handler)

    for name in ("api", "tools", "rag", "agent", "services"):
        logging.getLogger(name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
