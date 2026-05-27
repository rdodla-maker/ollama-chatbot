"""Lightweight workflow event bus and stable event envelope helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from queue import Queue
from threading import Lock
from typing import Any
from uuid import uuid4


_subscribers: dict[str, Queue] = {}
_lock = Lock()
_sequence = 0


def _next_sequence() -> int:
    global _sequence
    with _lock:
        _sequence += 1
        return _sequence


def subscribe() -> tuple[str, Queue]:
    subscriber_id = str(uuid4())
    q: Queue = Queue()
    with _lock:
        _subscribers[subscriber_id] = q
    return subscriber_id, q


def unsubscribe(subscriber_id: str) -> None:
    with _lock:
        _subscribers.pop(subscriber_id, None)


def _queue_snapshot() -> dict[str, Any]:
    try:
        from services.task_queue import get_queue_snapshot

        return get_queue_snapshot()
    except Exception:
        return {"size": 0, "pending": []}


def _status_payload() -> dict[str, Any]:
    from services.profile_store import list_profiles
    from services.workflow_status_service import build_workflow_status_payload

    records = list_profiles()
    return build_workflow_status_payload(records, _queue_snapshot())


def build_event_envelope(
    event_type: str,
    workflow_id: str | None = None,
    source: str = "workflow-engine",
    event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _status_payload()
    return {
        "type": "workflow.event",
        "contract": payload.get("transport", {}).get("contract", "workflow-status-payload-v1"),
        "sequence": _next_sequence(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "workflow_id": workflow_id,
        "source": source,
        "event": event or {},
        "payload": payload,
    }


def publish_event(
    event_type: str,
    workflow_id: str | None = None,
    source: str = "workflow-engine",
    event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    envelope = build_event_envelope(event_type, workflow_id=workflow_id, source=source, event=event)
    with _lock:
        targets = list(_subscribers.values())
    for q in targets:
        q.put(envelope)
    return envelope


def build_snapshot_event(source: str = "workflow-status") -> dict[str, Any]:
    return build_event_envelope("workflow.snapshot", source=source, event={"kind": "snapshot"})
