"""Workflow event search, lookup, pagination, and aggregation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _normalize_filters(filters: dict[str, Any] | None = None) -> dict[str, str]:
    return {key: str(value).strip() for key, value in (filters or {}).items() if value not in (None, "")}


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def flatten_workflow_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for record in records:
        for item in record.get("workflow_history") or []:
            metadata = item.get("metadata") or {}
            events.append(
                {
                    "workflow_id": record.get("id"),
                    "filename": record.get("uploaded_filename"),
                    "timestamp": item.get("when"),
                    "status": item.get("status") or record.get("status"),
                    "stage": metadata.get("stage") or item.get("status") or "queued",
                    "label": metadata.get("label") or (metadata.get("stage") or item.get("status") or "event").replace("_", " ").title(),
                    "state": metadata.get("state") or item.get("status") or "completed",
                    "source": metadata.get("source", "workflow-engine"),
                    "event_type": metadata.get("event_type") or item.get("status") or "workflow.event",
                    "severity": metadata.get("severity", "info"),
                    "owner": metadata.get("owner", "workflow-engine"),
                    "reason": metadata.get("reason") or metadata.get("failure_reason"),
                    "metadata": metadata,
                }
            )
    events.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return events


def filter_workflow_records(records: list[dict[str, Any]], filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    normalized = _normalize_filters(filters)
    if not normalized:
        return records

    def include(record: dict[str, Any]) -> bool:
        history = record.get("workflow_history") or []
        current = history[-1] if history else {"metadata": {}, "status": record.get("status")}
        metadata = current.get("metadata") or {}
        checks = {
            "workflow_id": record.get("id"),
            "stage": metadata.get("stage") or current.get("status") or record.get("status"),
            "severity": metadata.get("severity", "info"),
            "event_type": metadata.get("event_type") or current.get("status") or record.get("status"),
            "status": current.get("status") or record.get("status"),
        }
        for key, value in normalized.items():
            if key == "search":
                haystack = " ".join(
                    [
                        record.get("uploaded_filename") or "",
                        record.get("id") or "",
                        " ".join(record.get("target_roles") or []),
                        metadata.get("label") or "",
                        metadata.get("reason") or "",
                    ]
                ).lower()
                if value.lower() not in haystack:
                    return False
                continue
            if key in checks and str(checks[key] or "") != value:
                return False
        return True

    return [record for record in records if include(record)]


def search_workflow_events(
    records: list[dict[str, Any]],
    filters: dict[str, Any] | None = None,
    limit: int = 40,
    page: int = 1,
) -> dict[str, Any]:
    normalized = _normalize_filters(filters)
    events = flatten_workflow_events(records)

    def include(event: dict[str, Any]) -> bool:
        for key, value in normalized.items():
            if key == "search":
                haystack = " ".join(
                    [
                        event.get("workflow_id") or "",
                        event.get("filename") or "",
                        event.get("stage") or "",
                        event.get("event_type") or "",
                        event.get("label") or "",
                        event.get("reason") or "",
                    ]
                ).lower()
                if value.lower() not in haystack:
                    return False
                continue
            if key == "from_date":
                event_date = _parse_iso(event.get("timestamp"))
                target = _parse_iso(value)
                if not event_date or not target or event_date < target:
                    return False
                continue
            if key == "to_date":
                event_date = _parse_iso(event.get("timestamp"))
                target = _parse_iso(value)
                if not event_date or not target or event_date > target:
                    return False
                continue
            if key in event and str(event.get(key) or "") != value:
                return False
        return True

    filtered = [event for event in events if include(event)]
    page = max(page, 1)
    limit = max(limit, 1)
    start = (page - 1) * limit
    grouped = build_event_aggregations(filtered)
    return {
        "results": filtered[start:start + limit],
        "total": len(filtered),
        "filters": normalized,
        "page": page,
        "page_size": limit,
        "pages": max((len(filtered) + limit - 1) // limit, 1),
        "aggregations": grouped,
    }


def build_event_aggregations(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, int]] = {
        "workflow_id": {},
        "stage": {},
        "severity": {},
        "event_type": {},
    }
    for event in events:
        for key in grouped:
            value = str(event.get(key) or "unknown")
            grouped[key][value] = grouped[key].get(value, 0) + 1
    return {
        key: sorted(
            [{"key": item_key, "count": count} for item_key, count in counts.items()],
            key=lambda item: item["count"],
            reverse=True,
        )
        for key, counts in grouped.items()
    }