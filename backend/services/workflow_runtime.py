"""In-memory workflow runtime controls for queue and cancellation handling."""

from __future__ import annotations

from threading import Lock
from typing import Any


_controls: dict[str, dict[str, Any]] = {}
_lock = Lock()


def _ensure(upload_id: str) -> dict[str, Any]:
    with _lock:
        return _controls.setdefault(
            upload_id,
            {
                "cancel_requested": False,
                "active": False,
                "last_error": None,
            },
        )


def get_runtime_state(upload_id: str | None) -> dict[str, Any]:
    if not upload_id:
        return {"cancel_requested": False, "active": False, "last_error": None}
    with _lock:
        return dict(_controls.get(upload_id, {"cancel_requested": False, "active": False, "last_error": None}))


def mark_active(upload_id: str | None, active: bool) -> None:
    if not upload_id:
        return
    state = _ensure(upload_id)
    with _lock:
        state["active"] = active


def request_cancel(upload_id: str | None) -> None:
    if not upload_id:
        return
    state = _ensure(upload_id)
    with _lock:
        state["cancel_requested"] = True


def clear_cancel(upload_id: str | None) -> None:
    if not upload_id:
        return
    state = _ensure(upload_id)
    with _lock:
        state["cancel_requested"] = False


def set_last_error(upload_id: str | None, reason: str | None) -> None:
    if not upload_id:
        return
    state = _ensure(upload_id)
    with _lock:
        state["last_error"] = reason
