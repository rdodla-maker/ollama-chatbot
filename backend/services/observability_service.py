"""Operational observability, diagnostics, and aggregation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from services.worker_registry_service import snapshot_registry
from services.workflow_query_service import flatten_workflow_events


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _duration_seconds(start: str | None, end: str | None) -> float | None:
    start_dt = _parse_iso(start)
    end_dt = _parse_iso(end)
    if not start_dt or not end_dt:
        return None
    return max((end_dt - start_dt).total_seconds(), 0.0)


def build_observability_snapshot(records: list[dict[str, Any]], queue_snapshot: dict[str, Any]) -> dict[str, Any]:
    events = flatten_workflow_events(records)
    failures = [event for event in events if event.get("severity") == "error" or event.get("status") == "failed"]
    event_type_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    stage_counts: dict[str, int] = {}
    failure_reasons: dict[str, int] = {}
    ownership_counts: dict[str, int] = {}
    retry_owners: dict[str, int] = {}
    action_audit: list[dict[str, Any]] = []

    for event in events:
        event_type = event.get("event_type") or "workflow.event"
        severity = event.get("severity") or "info"
        stage = event.get("stage") or "workflow"
        owner = event.get("metadata", {}).get("worker_owner") or event.get("owner") or "workflow-engine"
        action = event.get("metadata", {}).get("action")

        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        ownership_counts[owner] = ownership_counts.get(owner, 0) + 1
        if action in {"retry", "restart", "resume", "cancel", "pause"}:
            retry_owners[owner] = retry_owners.get(owner, 0) + 1
            action_audit.append(
                {
                    "workflow_id": event.get("workflow_id"),
                    "timestamp": event.get("timestamp"),
                    "action": action,
                    "owner": owner,
                    "stage": stage,
                    "event_type": event_type,
                }
            )
        if event.get("reason"):
            failure_reasons[event["reason"]] = failure_reasons.get(event["reason"], 0) + 1

    worker_snapshot = snapshot_registry()
    return {
        "execution_logs": {
            "total_events": len(events),
            "recent_failures": failures[:8],
            "action_audit": action_audit[:20],
        },
        "orchestration_metrics": {
            "queue_depth": queue_snapshot.get("size", 0),
            "active_leases": len(worker_snapshot.get("leases", [])),
            "owned_workflows": len({lease.get("workflow_id") for lease in worker_snapshot.get("leases", [])}),
        },
        "worker_metrics": worker_snapshot,
        "failure_analytics": {
            "total_failures": len(failures),
            "top_reasons": sorted(
                [{"reason": reason, "count": count} for reason, count in failure_reasons.items()],
                key=lambda item: item["count"],
                reverse=True,
            )[:5],
        },
        "event_statistics": {
            "by_type": event_type_counts,
            "by_severity": severity_counts,
            "by_stage": stage_counts,
        },
        "workflow_audit": {
            "workflow_ownership": sorted(
                [{"owner": owner, "count": count} for owner, count in ownership_counts.items()],
                key=lambda item: item["count"],
                reverse=True,
            ),
            "retry_ownership": sorted(
                [{"owner": owner, "count": count} for owner, count in retry_owners.items()],
                key=lambda item: item["count"],
                reverse=True,
            ),
        },
    }


def build_failure_diagnostics(record: dict[str, Any]) -> dict[str, Any]:
    history = record.get("workflow_history") or []
    failures = [event for event in history if event.get("status") == "failed" or (event.get("metadata") or {}).get("severity") == "error"]
    if not failures:
        return {}
    latest = failures[-1]
    metadata = latest.get("metadata") or {}
    trace = []
    for event in history[-8:]:
        event_meta = event.get("metadata") or {}
        trace.append(
            {
                "timestamp": event.get("when"),
                "stage": event_meta.get("stage") or event.get("status"),
                "event_type": event_meta.get("event_type") or event.get("status"),
                "state": event_meta.get("state") or event.get("status"),
                "reason": event_meta.get("reason") or event_meta.get("failure_reason"),
                "worker_owner": event_meta.get("worker_owner"),
            }
        )

    suggestions = []
    failed_stage = metadata.get("stage") or latest.get("status") or "workflow"
    if failed_stage in {"ats_analysis", "analysis_started"}:
        suggestions.append("Retry ATS analysis from the failed checkpoint.")
    if failed_stage in {"parsing_started", "skills_extracted"}:
        suggestions.append("Retry parsing or resume from the parsing checkpoint.")
    suggestions.append("Inspect the event explorer for correlated worker and stage events.")

    return {
        "failure_reason": metadata.get("reason") or metadata.get("failure_reason"),
        "failed_stage": failed_stage,
        "recovery_suggestions": suggestions,
        "retry_options": [item for item in record.get("available_actions") or [] if item.get("action") in {"retry", "restart", "resume"}],
        "execution_trace": trace,
    }


def build_performance_drilldown(records: list[dict[str, Any]]) -> dict[str, Any]:
    workflow_durations: list[dict[str, Any]] = []
    stage_durations: dict[str, list[float]] = {}
    failure_hotspots: dict[str, int] = {}
    retry_heavy: list[dict[str, Any]] = []

    for record in records:
        history = record.get("workflow_history") or []
        if history:
            duration = _duration_seconds(history[0].get("when"), history[-1].get("when"))
            workflow_durations.append(
                {
                    "workflow_id": record.get("id"),
                    "uploaded_filename": record.get("uploaded_filename"),
                    "duration_seconds": round(duration or 0, 2),
                }
            )
            retries = sum(1 for event in history if (event.get("metadata") or {}).get("action") in {"retry", "restart", "resume"})
            if retries:
                retry_heavy.append(
                    {
                        "workflow_id": record.get("id"),
                        "uploaded_filename": record.get("uploaded_filename"),
                        "retry_count": retries,
                    }
                )
            for index, event in enumerate(history[:-1]):
                metadata = event.get("metadata") or {}
                stage = metadata.get("stage") or event.get("status") or "workflow"
                duration = _duration_seconds(event.get("when"), history[index + 1].get("when"))
                if duration is not None:
                    stage_durations.setdefault(stage, []).append(duration)
            for event in history:
                metadata = event.get("metadata") or {}
                if event.get("status") == "failed" or metadata.get("severity") == "error":
                    stage = metadata.get("stage") or event.get("status") or "workflow"
                    failure_hotspots[stage] = failure_hotspots.get(stage, 0) + 1

    workflow_durations.sort(key=lambda item: item["duration_seconds"], reverse=True)
    retry_heavy.sort(key=lambda item: item["retry_count"], reverse=True)

    return {
        "average_stage_duration": sorted(
            [
                {
                    "stage": stage,
                    "average_duration_seconds": round(sum(values) / len(values), 2),
                    "samples": len(values),
                }
                for stage, values in stage_durations.items()
                if values
            ],
            key=lambda item: item["average_duration_seconds"],
            reverse=True,
        ),
        "slowest_workflows": workflow_durations[:5],
        "retry_heavy_workflows": retry_heavy[:5],
        "failure_hotspots": sorted(
            [{"stage": stage, "count": count} for stage, count in failure_hotspots.items()],
            key=lambda item: item["count"],
            reverse=True,
        )[:5],
    }