"""Lightweight workflow event bus and stable event envelope helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from queue import Queue
from threading import Lock
from typing import Any
from uuid import uuid4

from services.workflow_contracts import (
    WORKFLOW_EVENT_CONTRACT,
    WORKFLOW_EVENT_VERSION,
    WORKFLOW_STATUS_CONTRACT,
    normalize_event_metadata,
    normalize_source,
)


_subscribers: dict[str, dict[str, Any]] = {}
_lock = Lock()
_sequence = 0


def _next_sequence() -> int:
    global _sequence
    with _lock:
        _sequence += 1
        return _sequence


def subscribe(
    workflow_id: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    stage: str | None = None,
    severity: str | None = None,
    status: str | None = None,
) -> tuple[str, Queue]:
    subscriber_id = str(uuid4())
    q: Queue = Queue()
    with _lock:
        _subscribers[subscriber_id] = {
            "queue": q,
            "workflow_id": workflow_id,
            "event_type": event_type,
            "source": source,
            "stage": stage,
            "severity": severity,
            "status": status,
        }
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
    event_payload = event or {}
    metadata = normalize_event_metadata(
        event_payload.get("metadata") or {},
        event_type=event_type,
        stage=event_payload.get("stage"),
        status=event_payload.get("status"),
        source=event_payload.get("source") or source,
        owner=event_payload.get("owner"),
        severity=event_payload.get("severity"),
    )
    stage = metadata.get("stage")
    status = metadata.get("status")
    severity = metadata.get("severity")
    source = normalize_source(metadata.get("source") or source)
    return {
        "type": "workflow.event",
        "contract": payload.get("transport", {}).get("contract", WORKFLOW_STATUS_CONTRACT),
        "event_contract": WORKFLOW_EVENT_CONTRACT,
        "event_version": WORKFLOW_EVENT_VERSION,
        "sequence": _next_sequence(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "workflow_id": workflow_id,
        "source": source,
        "stage": stage,
        "status": status,
        "severity": severity,
        "event": {**event_payload, "metadata": metadata},
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
    for target in targets:
        if not _matches_filter(target, envelope):
            continue
        target["queue"].put(envelope)
    return envelope


def build_snapshot_event(source: str = "workflow-status") -> dict[str, Any]:
    return build_event_envelope("workflow.snapshot", source=source, event={"kind": "snapshot"})


def _matches_filter(subscription: dict[str, Any], envelope: dict[str, Any]) -> bool:
    workflow_filter = subscription.get("workflow_id")
    if workflow_filter and workflow_filter != envelope.get("workflow_id"):
        return False

    event_filter = subscription.get("event_type")
    if event_filter and event_filter != envelope.get("event_type"):
        return False

    source_filter = subscription.get("source")
    if source_filter and source_filter != envelope.get("source"):
        return False

    stage_filter = subscription.get("stage")
    if stage_filter and stage_filter != envelope.get("stage"):
        return False

    severity_filter = subscription.get("severity")
    if severity_filter and severity_filter != envelope.get("severity"):
        return False

    status_filter = subscription.get("status")
    if status_filter and status_filter != envelope.get("status"):
        return False

    return True
