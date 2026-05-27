"""
Legacy MongoDB connection module (motor AsyncIOMotorClient).

This project now uses SQLite + SQLAlchemy by default. The original MongoDB
connection file has been retained as a placeholder for future optional
integration, but it is no longer used by the application. To re-enable,
restore the original content and set `MONGODB_URL`/`DATABASE_NAME` in your environment.

NOTE: Keeping a lightweight placeholder avoids accidental imports during
cleanup while preserving context for future migrations.
"""

from typing import Any


def get_database() -> Any:
    """Return a benign placeholder for legacy imports."""
    return None