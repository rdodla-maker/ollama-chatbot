"""
Pending file edits — require human approval before writing to disk.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from core.logging_config import get_logger
from core.security import read_text_file_limited, resolve_safe_path

logger = get_logger("services")


class ChangeStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class PendingChange:
    id: str
    file_path: str
    new_content: str
    status: ChangeStatus = ChangeStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    original_preview: str = ""


# In-memory store (persist to disk in Wave 4 if needed)
_store: dict[str, PendingChange] = {}


def propose_file_edit(file_path: str, new_content: str) -> str:
    """
    Stage a file edit for approval. Does not write to disk.
    Returns change ID and summary message.
    """
    safe_path = resolve_safe_path(file_path)
    rel = str(safe_path)

    original_preview = ""
    if safe_path.is_file():
        try:
            original_preview = read_text_file_limited(safe_path, max_bytes=2000)
        except Exception:
            original_preview = "(could not read existing file)"

    change_id = str(uuid.uuid4())[:8]
    _store[change_id] = PendingChange(
        id=change_id,
        file_path=rel,
        new_content=new_content,
        original_preview=original_preview[:500],
    )

    logger.info("Proposed file edit %s for %s", change_id, rel)
    return (
        f"Change {change_id} proposed for {rel}. "
        f"Awaiting approval via POST /pending-changes/{change_id}/approve"
    )


def list_pending() -> list[dict]:
    return [
        {
            "id": c.id,
            "file_path": c.file_path,
            "status": c.status.value,
            "created_at": c.created_at,
            "preview": c.new_content[:200],
        }
        for c in _store.values()
        if c.status == ChangeStatus.PENDING
    ]


def get_change(change_id: str) -> PendingChange | None:
    return _store.get(change_id)


def approve_change(change_id: str) -> dict:
    change = _store.get(change_id)
    if not change:
        raise ValueError(f"Change {change_id} not found.")
    if change.status != ChangeStatus.PENDING:
        raise ValueError(f"Change {change_id} is already {change.status.value}.")

    path = resolve_safe_path(change.file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(change.new_content, encoding="utf-8")
    change.status = ChangeStatus.APPROVED
    logger.info("Approved and applied change %s to %s", change_id, path)
    return {"id": change_id, "file_path": str(path), "status": "approved"}


def reject_change(change_id: str) -> dict:
    change = _store.get(change_id)
    if not change:
        raise ValueError(f"Change {change_id} not found.")
    change.status = ChangeStatus.REJECTED
    logger.info("Rejected change %s", change_id)
    return {"id": change_id, "status": "rejected"}
