"""Workflow action handling and safe state transitions."""

from __future__ import annotations

from typing import Any

from services.profile_store import list_profiles, update_profile
from services.workflow_contracts import build_transport_capabilities as build_contract_transport_capabilities, normalize_event_metadata
from services.workflow_runtime import clear_cancel, clear_pause, request_cancel, request_pause

RETRY_LIMIT = 3
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
RESUMABLE_STAGES = {"processing", "parsing_started", "skills_extracted", "ats_analysis", "optimization_ready"}


def _find_record(workflow_id: str) -> dict[str, Any] | None:
    for record in list_profiles():
        if record.get("id") == workflow_id:
            return record
    return None


def _workflow_events(record: dict[str, Any]) -> list[dict[str, Any]]:
    return record.get("workflow_history") or []


def _current_stage(record: dict[str, Any]) -> str:
    events = _workflow_events(record)
    if not events:
        return record.get("status") or "queued"
    metadata = events[-1].get("metadata") or {}
    return metadata.get("stage") or events[-1].get("status") or record.get("status") or "queued"


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


def _resolve_retry_stage(action: str, stage: str | None, paused_metadata: dict[str, Any], current_stage: str) -> str:
    if action == "restart":
        return "processing"
    candidate = stage or paused_metadata.get("resume_stage") or ("ats_analysis" if action == "retry" else current_stage)
    if action == "retry" and candidate not in RETRYABLE_STAGES:
        raise ValueError("Retry stage is not supported")
    if action == "resume" and candidate not in RESUMABLE_STAGES:
        raise ValueError("Resume stage is not supported")
    return candidate


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
    items.append(
        {
            "action": "pause",
            "label": "Pause",
            "enabled": state in {"queued", "processing", "retrying"},
            "reason": None if state in {"queued", "processing", "retrying"} else "Pause is only available for queued or active workflows.",
        }
    )
    items.append(
        {
            "action": "resume",
            "label": "Resume",
            "enabled": state == "paused",
            "reason": None if state == "paused" else "Resume is only available after a workflow has been paused.",
        }
    )
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
    from services.workflow_execution_service import record_failure as execution_record_failure

    execution_record_failure(workflow_id, reason, stage=stage)


def apply_workflow_action(workflow_id: str, action: str, stage: str | None = None) -> dict[str, Any]:
    record = _find_record(workflow_id)
    if not record:
        raise ValueError("Workflow not found")

    available = {item["action"]: item for item in get_available_actions(record)}
    selected = available.get(action)
    if not selected or not selected.get("enabled"):
        raise ValueError(selected.get("reason") if selected else "Action is not available")

    from services.task_queue import cancel_queued_workflow, enqueue_task

    retry_count = _retry_count(record)
    upload_id = record.get("uploaded_filename")
    target_roles = record.get("target_roles") or []
    current_stage = _current_stage(record)
    paused_metadata = (_workflow_events(record)[-1].get("metadata") or {}) if _workflow_events(record) else {}
    retry_stage = _resolve_retry_stage(action, stage, paused_metadata, current_stage)

    if action == "cancel":
        request_cancel(upload_id)
        removed = cancel_queued_workflow(workflow_id, upload_id)
        update_profile(
            workflow_id,
            {
                "status": "cancelled",
                "target_roles": target_roles,
                "metadata": normalize_event_metadata(
                    event_type="workflow.cancelled",
                    stage="cancelled",
                    status="cancelled",
                    source="workflow-engine",
                    owner="workflow-engine",
                    severity="warning",
                    lifecycle="cancelled",
                    extra={
                        "label": "Workflow cancelled",
                        "progress": 100 if removed else 70,
                        "state": "cancelled",
                        "action": action,
                        "reason": "Cancelled by user",
                    },
                ),
            },
        )
        return {
            "workflow_id": workflow_id,
            "action": action,
            "status": "cancelled",
            "message": "Workflow cancelled.",
            "stage": None,
        }

    if action == "pause":
        request_pause(upload_id)
        removed = cancel_queued_workflow(workflow_id, upload_id)
        update_profile(
            workflow_id,
            {
                "status": "paused",
                "target_roles": target_roles,
                "metadata": normalize_event_metadata(
                    event_type="workflow.paused",
                    stage="paused",
                    status="paused",
                    source="workflow-engine",
                    owner="workflow-engine",
                    severity="warning",
                    lifecycle="paused",
                    extra={
                        "label": "Workflow paused",
                        "progress": 25 if removed else 60,
                        "state": "paused",
                        "action": action,
                        "reason": "Paused by user",
                        "resume_stage": stage or current_stage,
                        "checkpoint_stage": current_stage,
                        "previous_stage": current_stage,
                    },
                ),
            },
        )
        return {
            "workflow_id": workflow_id,
            "action": action,
            "status": "paused",
            "message": "Workflow paused and checkpoint preserved.",
            "stage": stage or current_stage,
        }

    if action == "resume":
        clear_pause(upload_id)
        update_profile(
            workflow_id,
            {
                "status": "retrying",
                "target_roles": target_roles,
                "metadata": normalize_event_metadata(
                    event_type="workflow.resumed",
                    stage="retrying",
                    status="retrying",
                    source="workflow-engine",
                    owner="workflow-engine",
                    severity="info",
                    lifecycle="resume",
                    extra={
                        "label": "Workflow resume queued",
                        "progress": 35,
                        "state": "retrying",
                        "action": action,
                        "retry_stage": retry_stage,
                        "retry_count": retry_count,
                        "reason": _last_failure_reason(record),
                        "previous_stage": current_stage,
                    },
                ),
            },
        )
        enqueue_task(
            {
                "type": "analyze_resume",
                "upload_id": upload_id,
                "workflow_id": workflow_id,
                "target_roles": target_roles,
                "retry_count": retry_count,
                "retry_stage": retry_stage,
            }
        )
        return {
            "workflow_id": workflow_id,
            "action": action,
            "status": "queued",
            "message": f"Workflow queued to resume from {retry_stage.replace('_', ' ')}.",
            "stage": retry_stage,
        }

    attempt = retry_count + 1
    clear_cancel(upload_id)
    clear_pause(upload_id)
    update_profile(
        workflow_id,
        {
            "status": "retrying",
            "target_roles": target_roles,
            "metadata": normalize_event_metadata(
                event_type="retry.started",
                stage="retrying",
                status="retrying",
                source="workflow-engine",
                owner="workflow-engine",
                severity="warning" if action == "retry" else "info",
                lifecycle="retry",
                extra={
                    "label": "Workflow retry queued" if action == "retry" else "Workflow restart queued",
                    "progress": 25,
                    "state": "retrying",
                    "action": action,
                    "retry_stage": retry_stage,
                    "retry_count": attempt,
                    "reason": _last_failure_reason(record),
                    "previous_stage": current_stage,
                },
            ),
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
    return build_contract_transport_capabilities()
