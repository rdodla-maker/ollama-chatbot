"""Workflow action handling and safe state transitions."""

from __future__ import annotations

from typing import Any

from services.profile_store import list_profiles, update_profile
from services.workflow_runtime import clear_cancel, request_cancel

RETRY_LIMIT = 3
PLACEHOLDER_ACTIONS = {"pause", "resume"}
TERMINAL_STATES = {"completed", "failed", "cancelled"}
RETRYABLE_STAGES = {
    "parsing_started": "Retry parsing",
    "ats_analysis": "Retry ATS analysis",
    "optimization_ready": "Retry optimization",
}

FAILURE_EVENT_TYPES = {
    "parsing_started": "parsing.failed",
    "ats_analysis": "analysis.failed",
    "optimization_ready": "optimization.failed",
}


def _find_record(workflow_id: str) -> dict[str, Any] | None:
    for record in list_profiles():
        if record.get("id") == workflow_id:
            return record
    return None


def _workflow_events(record: dict[str, Any]) -> list[dict[str, Any]]:
    return record.get("workflow_history") or []


def _retry_count(record: dict[str, Any]) -> int:
    return sum(
        1
        for event in _workflow_events(record)
        if (event.get("metadata") or {}).get("action") in {"retry", "restart"}
    )


def _retry_history(record: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for event in _workflow_events(record):
        metadata = event.get("metadata") or {}
        if metadata.get("action") in {"retry", "restart"}:
            out.append(
                {
                    "action": metadata.get("action"),
                    "timestamp": event.get("when"),
                    "attempt": metadata.get("retry_count"),
                    "reason": metadata.get("reason"),
                }
            )
    return out


def _last_failure_reason(record: dict[str, Any]) -> str | None:
    for event in reversed(_workflow_events(record)):
        metadata = event.get("metadata") or {}
        if event.get("status") == "failed":
            return metadata.get("reason") or metadata.get("failure_reason")
    return None


def _normalized_state(record: dict[str, Any]) -> str:
    status = record.get("status") or "queued"
    if status in {"uploaded", "queued"}:
        return "queued"
    if status in {"parsing_started", "skills_extracted", "analysis_started", "processing"}:
        return "processing"
    if status in {"analysis_completed", "analyzed", "completed"}:
        return "completed"
    if status in {"failed"}:
        return "failed"
    if status in {"cancelled"}:
        return "cancelled"
    if status in {"retrying"}:
        return "retrying"
    if status in {"paused"}:
        return "paused"
    return status


def get_available_actions(record: dict[str, Any]) -> list[dict[str, Any]]:
    state = _normalized_state(record)
    retry_count = _retry_count(record)
    items = []

    items.append(
        {
            "action": "retry",
            "label": "Retry",
            "enabled": state in {"failed", "cancelled"} and retry_count < RETRY_LIMIT,
            "reason": None if state in {"failed", "cancelled"} and retry_count < RETRY_LIMIT else "Retry is only available after failure or cancellation.",
        }
    )
    items.append(
        {
            "action": "cancel",
            "label": "Cancel",
            "enabled": state in {"queued", "processing", "retrying"},
            "reason": None if state in {"queued", "processing", "retrying"} else "Cancel is only available for queued or active workflows.",
        }
    )
    items.append(
        {
            "action": "restart",
            "label": "Restart",
            "enabled": state in TERMINAL_STATES and retry_count < RETRY_LIMIT,
            "reason": None if state in TERMINAL_STATES and retry_count < RETRY_LIMIT else "Restart is only available for completed, failed, or cancelled workflows.",
        }
    )
    items.append({"action": "pause", "label": "Pause", "enabled": False, "reason": "Placeholder for future real-time worker controls."})
    items.append({"action": "resume", "label": "Resume", "enabled": False, "reason": "Placeholder for future real-time worker controls."})
    return items


def get_stage_retry_actions(record: dict[str, Any]) -> list[dict[str, Any]]:
    state = _normalized_state(record)
    retry_count = _retry_count(record)
    enabled = state in {"failed", "cancelled"} and retry_count < RETRY_LIMIT
    reason = None if enabled else "Stage retry is only available after failure or cancellation."
    return [
        {
            "action": "retry",
            "stage": stage,
            "label": label,
            "enabled": enabled,
            "reason": reason,
        }
        for stage, label in RETRYABLE_STAGES.items()
    ]


def record_failure(workflow_id: str, reason: str, stage: str | None = None) -> None:
    record = _find_record(workflow_id)
    if not record:
        return
    failed_stage = stage or "workflow"
    update_profile(
        workflow_id,
        {
            "status": "failed",
            "target_roles": record.get("target_roles") or [],
            "metadata": {
                "stage": failed_stage,
                "label": f"{failed_stage.replace('_', ' ').title()} failed",
                "progress": 100,
                "state": "failed",
                "reason": reason,
                "failure_reason": reason,
                "source": "workflow-engine",
                "event_type": FAILURE_EVENT_TYPES.get(failed_stage, f"{failed_stage}.failed"),
            },
        },
    )


def apply_workflow_action(workflow_id: str, action: str, stage: str | None = None) -> dict[str, Any]:
    record = _find_record(workflow_id)
    if not record:
        raise ValueError("Workflow not found")

    if action in PLACEHOLDER_ACTIONS:
        return {
            "workflow_id": workflow_id,
            "action": action,
            "status": "placeholder",
            "message": f"{action.title()} is reserved for future automation controls.",
            "stage": stage,
        }

    available = {item["action"]: item for item in get_available_actions(record)}
    selected = available.get(action)
    if not selected or not selected.get("enabled"):
        raise ValueError(selected.get("reason") if selected else "Action is not available")

    from services.task_queue import cancel_queued_workflow, enqueue_task

    retry_count = _retry_count(record)
    upload_id = record.get("uploaded_filename")
    target_roles = record.get("target_roles") or []
    retry_stage = stage or ("processing" if action == "restart" else "ats_analysis")

    if action == "cancel":
        request_cancel(upload_id)
        removed = cancel_queued_workflow(workflow_id, upload_id)
        update_profile(
            workflow_id,
            {
                "status": "cancelled",
                "target_roles": target_roles,
                "metadata": {
                    "stage": "cancelled",
                    "label": "Workflow cancelled",
                    "progress": 100 if removed else 70,
                    "state": "cancelled",
                    "action": action,
                    "reason": "Cancelled by user",
                    "source": "workflow-engine",
                    "event_type": "workflow.cancelled",
                },
            },
        )
        return {
            "workflow_id": workflow_id,
            "action": action,
            "status": "cancelled",
            "message": "Workflow cancelled.",
            "stage": None,
        }

    attempt = retry_count + 1
    clear_cancel(upload_id)
    update_profile(
        workflow_id,
        {
            "status": "retrying",
            "target_roles": target_roles,
            "metadata": {
                "stage": "retrying",
                "label": "Workflow retry queued" if action == "retry" else "Workflow restart queued",
                "progress": 25,
                "state": "retrying",
                "action": action,
                "retry_stage": retry_stage,
                "retry_count": attempt,
                "reason": _last_failure_reason(record),
                "source": "workflow-engine",
                "event_type": "retry.started",
            },
        },
    )
    enqueue_task(
        {
            "type": "analyze_resume",
            "upload_id": upload_id,
            "workflow_id": workflow_id,
            "target_roles": target_roles,
            "retry_count": attempt,
            "retry_stage": retry_stage,
        }
    )
    return {
        "workflow_id": workflow_id,
        "action": action,
        "status": "queued",
        "message": (
            f"Workflow queued for {retry_stage.replace('_', ' ')} retry."
            if action == "retry"
            else "Workflow queued for restart."
        ),
        "stage": retry_stage,
    }


def build_transport_capabilities() -> dict[str, Any]:
    return {
        "mode": "sse-primary",
        "supported": ["polling", "sse", "websocket-ready", "multi-client-ready"],
        "contract": "workflow-status-payload-v1",
    }
