"""Reusable SSE workflow streaming service."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from queue import Empty
from typing import Any

from fastapi import Request
from sse_starlette.event import ServerSentEvent

from services.workflow_event_bus import build_snapshot_event, subscribe, unsubscribe
from services.workflow_analytics_service import build_workflow_analytics
from services.observability_service import build_failure_diagnostics, build_observability_snapshot
from services.workflow_query_service import filter_workflow_records, search_workflow_events
from services.workflow_status_service import build_workflow_status_payload


def _sse_message(payload: dict[str, Any], event_name: str | None = None) -> ServerSentEvent:
    return ServerSentEvent(data=json.dumps(payload), event=event_name)


def heartbeat_event() -> dict[str, Any]:
    return {
        "type": "heartbeat",
        "timestamp": asyncio.get_running_loop().time(),
    }


def _build_filtered_payload(filters: dict[str, Any]) -> dict[str, Any]:
    from services.profile_store import list_profiles
    from services.task_queue import get_queue_snapshot

    records = list_profiles()
    queue_snapshot = get_queue_snapshot()
    enriched_records = [{**record, "failure_diagnostics": build_failure_diagnostics(record)} for record in records]
    filtered_records = filter_workflow_records(enriched_records, filters)
    return build_workflow_status_payload(
        filtered_records,
        queue_snapshot,
        analytics=build_workflow_analytics(filtered_records),
        observability=build_observability_snapshot(filtered_records, queue_snapshot),
        event_query=search_workflow_events(enriched_records, filters),
        active_filters={key: value for key, value in filters.items() if value},
    )


def _filtered_envelope(envelope: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any]:
    if not any(filters.values()):
        return envelope
    return {
        **envelope,
        "payload": _build_filtered_payload(filters),
    }


async def stream_workflow_events(
    request: Request,
    workflow_id: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    stage: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    search: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> AsyncIterator[ServerSentEvent]:
    filters = {
        "workflow_id": workflow_id,
        "event_type": event_type,
        "stage": stage,
        "severity": severity,
        "status": status,
        "search": search,
        "from_date": from_date,
        "to_date": to_date,
    }
    subscriber_id, event_queue = subscribe(
        workflow_id=workflow_id,
        event_type=event_type,
        source=source,
        stage=stage,
        severity=severity,
        status=status,
    )
    try:
        snapshot = _filtered_envelope(build_snapshot_event(), filters)
        yield _sse_message(snapshot, snapshot.get("event_type"))
        while True:
            if await request.is_disconnected():
                break
            try:
                envelope = await asyncio.wait_for(
                    asyncio.to_thread(event_queue.get, True, 10),
                    timeout=12,
                )
                envelope = _filtered_envelope(envelope, filters)
                yield _sse_message(envelope, envelope.get("event_type"))
            except (asyncio.TimeoutError, Empty):
                heartbeat = heartbeat_event()
                yield _sse_message(heartbeat, heartbeat.get("type"))
    finally:
        unsubscribe(subscriber_id)