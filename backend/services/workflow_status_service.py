"""Workflow status shaping for the Mission Control dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any


DEFAULT_STAGE_LABELS = {
    "resume_uploaded": "Resume uploaded",
    "processing": "Workflow processing",
    "parsing_started": "Parsing started",
    "skills_extracted": "Skills extracted",
    "ats_analysis": "ATS analysis completed",
    "optimization_ready": "Optimization ready",
    "analysis_completed": "Optimization ready",
    "queued": "Workflow queued",
    "failed": "Workflow failed",
    "cancelled": "Workflow cancelled",
    "retrying": "Workflow retry queued",
    "paused": "Workflow paused",
}

STATUS_TO_STAGE = {
    "uploaded": {"stage": "resume_uploaded", "progress": 10, "state": "completed"},
    "queued": {"stage": "queued", "progress": 15, "state": "queued"},
    "processing": {"stage": "processing", "progress": 15, "state": "processing"},
    "parsing_started": {"stage": "parsing_started", "progress": 20, "state": "running"},
    "skills_extracted": {"stage": "skills_extracted", "progress": 45, "state": "completed"},
    "analysis_started": {"stage": "ats_analysis", "progress": 60, "state": "running"},
    "analysis_completed": {"stage": "optimization_ready", "progress": 100, "state": "completed"},
    "analyzed": {"stage": "optimization_ready", "progress": 100, "state": "completed"},
    "failed": {"stage": "failed", "progress": 100, "state": "failed"},
    "cancelled": {"stage": "cancelled", "progress": 100, "state": "cancelled"},
    "retrying": {"stage": "retrying", "progress": 25, "state": "retrying"},
    "paused": {"stage": "paused", "progress": 50, "state": "paused"},
}


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


def _coerce_event(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata") or {}
    mapping = STATUS_TO_STAGE.get(event.get("status"), {})
    stage = metadata.get("stage") or mapping.get("stage") or event.get("status") or "queued"
    label = metadata.get("label") or DEFAULT_STAGE_LABELS.get(stage) or stage.replace("_", " ").title()
    progress = metadata.get("progress")
    if progress is None:
        progress = mapping.get("progress", 0)
    state = metadata.get("state") or mapping.get("state") or "completed"
    return {
        "timestamp": event.get("when"),
        "status": event.get("status") or stage,
        "stage": stage,
        "label": label,
        "progress": progress,
        "state": state,
        "duration_seconds": event.get("duration_seconds"),
        "metadata": metadata,
    }


def _enrich_timeline(history: list[dict[str, Any]], created_at: str | None) -> list[dict[str, Any]]:
    events = [_coerce_event(event) for event in history or []]
    if not events and created_at:
        events = [
            {
                "timestamp": created_at,
                "status": "uploaded",
                "stage": "resume_uploaded",
                "label": DEFAULT_STAGE_LABELS["resume_uploaded"],
                "progress": 10,
                "state": "completed",
                "duration_seconds": None,
                "metadata": {},
            }
        ]
    for index, event in enumerate(events):
        next_timestamp = events[index + 1]["timestamp"] if index + 1 < len(events) else None
        if event["duration_seconds"] is None:
            event["duration_seconds"] = _duration_seconds(event["timestamp"], next_timestamp)
    return events


def build_workflow_profile(record: dict[str, Any]) -> dict[str, Any]:
    from services.workflow_orchestration_service import (
        get_available_actions,
        get_stage_retry_actions,
        _retry_count,
        _retry_history,
        _last_failure_reason,
    )

    timeline = _enrich_timeline(record.get("workflow_history") or [], record.get("created_at"))
    current_event = timeline[-1] if timeline else {
        "stage": "queued",
        "label": "Workflow queued",
        "progress": 0,
        "state": "queued",
        "timestamp": record.get("created_at"),
        "status": record.get("status") or "queued",
        "duration_seconds": None,
        "metadata": {},
    }
    started_at = timeline[0]["timestamp"] if timeline else record.get("created_at")
    last_activity = current_event.get("timestamp") or record.get("updated_at") or record.get("created_at")
    workflow_duration_seconds = _duration_seconds(started_at, last_activity)
    queued_actions = []
    if current_event.get("progress", 0) < 100 and current_event.get("state") not in {"failed", "cancelled"}:
        queued_actions.append("Awaiting next workflow stage")
    if not record.get("ats_score"):
        queued_actions.append("ATS scoring refresh")

    retry_count = _retry_count(record)
    retry_history = _retry_history(record)
    failure_reason = _last_failure_reason(record)

    analysis = record.get("profile") or {}
    execution_metadata = {
        "event_count": len(timeline),
        "started_at": started_at,
        "last_activity": last_activity,
        "workflow_duration_seconds": workflow_duration_seconds,
        "role_count": len(record.get("target_roles") or []),
        "ats_score": record.get("ats_score") or analysis.get("ats_score"),
        "last_state": current_event.get("state"),
        "retry_count": retry_count,
        "failure_reason": failure_reason,
        "recovery_state": "recoverable" if current_event.get("state") in {"failed", "cancelled"} and retry_count < 3 else "stable",
    }
    summary_bits = [current_event.get("label")]
    if execution_metadata["ats_score"] is not None:
        summary_bits.append(f"ATS {execution_metadata['ats_score']}")
    if record.get("target_roles"):
        summary_bits.append(f"Roles: {', '.join(record['target_roles'][:2])}")

    return {
        "id": record.get("id"),
        "uploaded_filename": record.get("uploaded_filename"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at") or last_activity,
        "status": record.get("status") or current_event.get("status") or "queued",
        "target_roles": record.get("target_roles") or [],
        "profile": record.get("profile"),
        "ats_score": record.get("ats_score") or analysis.get("ats_score"),
        "progress_percentage": current_event.get("progress", 0),
        "current_stage": current_event.get("stage"),
        "current_stage_label": current_event.get("label"),
        "current_stage_state": current_event.get("state"),
        "workflow_duration_seconds": workflow_duration_seconds,
        "last_activity": last_activity,
        "queued_actions": queued_actions,
        "execution_metadata": execution_metadata,
        "execution_summary": " | ".join([part for part in summary_bits if part]),
        "timeline": timeline,
        "available_actions": get_available_actions(record),
        "stage_actions": get_stage_retry_actions(record),
        "retry_count": retry_count,
        "retry_history": retry_history,
        "failure_reason": failure_reason,
    }


def build_workflow_status_payload(records: list[dict[str, Any]], queue_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    from services.workflow_orchestration_service import build_transport_capabilities

    profiles = [build_workflow_profile(record) for record in records]
    profiles.sort(key=lambda item: item.get("last_activity") or item.get("created_at") or "", reverse=True)
    activity_feed = []
    for profile in profiles:
        for event in profile.get("timeline", [])[-4:]:
            activity_feed.append(
                {
                    "workflow_id": profile.get("id"),
                    "filename": profile.get("uploaded_filename"),
                    "timestamp": event.get("timestamp"),
                    "status": event.get("status"),
                    "stage": event.get("stage"),
                    "label": event.get("label"),
                    "state": event.get("state"),
                    "source": event.get("metadata", {}).get("source", "workflow-engine"),
                    "event_type": event.get("metadata", {}).get("event_type", event.get("status")),
                }
            )
    activity_feed.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    overview = {
        "active": sum(1 for item in profiles if item.get("current_stage_state") in {"running", "processing", "retrying"}),
        "completed": sum(1 for item in profiles if item.get("progress_percentage") == 100 and item.get("current_stage_state") == "completed"),
        "failed": sum(1 for item in profiles if item.get("current_stage_state") == "failed" or item.get("status") == "failed"),
        "queued": sum(1 for item in profiles if item.get("current_stage_state") == "queued" or item.get("status") == "queued"),
        "total": len(profiles),
    }
    return {
        "profiles": profiles,
        "activity_feed": activity_feed[:20],
        "overview": overview,
        "queue": queue_snapshot or {"size": 0, "pending": []},
        "automation_placeholders": {
            "n8n_monitoring": "ready",
            "automation_queue": "ready",
            "scheduled_workflows": "planned",
            "background_jobs": "connected_to_in_memory_worker",
        },
        "transport": build_transport_capabilities(),
    }