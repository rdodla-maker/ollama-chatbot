"""Workflow execution engine with lifecycle control and recovery support."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from core.config import settings
from services.profile_store import list_profiles, update_profile
from services.workflow_contracts import normalize_event_metadata

STAGE_SEQUENCE = ["queued", "processing", "parsing_started", "skills_extracted", "ats_analysis", "optimization_ready"]
TERMINAL_STAGES = {"optimization_ready", "failed", "cancelled"}
STAGE_TIMEOUTS = {
    "processing": 5,
    "parsing_started": 10,
    "skills_extracted": 10,
    "ats_analysis": 120,
    "optimization_ready": 30,
}
STAGE_DEFINITIONS = {
    "processing": {
        "status": "processing",
        "label": "Workflow processing",
        "progress": 15,
        "state": "processing",
        "event_type": "workflow.processing",
        "severity": "info",
        "owner": "workflow-engine",
    },
    "parsing_started": {
        "status": "parsing_started",
        "label": "Parsing started",
        "progress": 20,
        "state": "running",
        "event_type": "parsing.started",
        "severity": "info",
        "owner": "parser",
    },
    "skills_extracted": {
        "status": "skills_extracted",
        "label": "Skills extracted",
        "progress": 45,
        "state": "completed",
        "event_type": "parsing.completed",
        "severity": "info",
        "owner": "parser",
    },
    "ats_analysis": {
        "status": "analysis_started",
        "label": "ATS analysis started",
        "progress": 60,
        "state": "running",
        "event_type": "analysis.started",
        "severity": "info",
        "owner": "analysis-engine",
    },
    "optimization_ready": {
        "status": "analysis_completed",
        "label": "Optimization ready",
        "progress": 100,
        "state": "completed",
        "event_type": "optimization.completed",
        "severity": "info",
        "owner": "analysis-engine",
    },
}
ALLOWED_TRANSITIONS = {
    "queued": {"processing"},
    "resume_uploaded": {"processing"},
    "processing": {"parsing_started", "failed", "cancelled"},
    "parsing_started": {"skills_extracted", "failed", "cancelled"},
    "skills_extracted": {"ats_analysis", "failed", "cancelled"},
    "ats_analysis": {"optimization_ready", "failed", "cancelled"},
    "optimization_ready": set(),
    "failed": {"processing", "parsing_started", "ats_analysis", "optimization_ready"},
    "cancelled": {"processing", "parsing_started", "ats_analysis", "optimization_ready"},
    "retrying": {"processing", "parsing_started", "ats_analysis", "optimization_ready"},
    "paused": {"processing", "parsing_started", "skills_extracted", "ats_analysis", "optimization_ready"},
}


def _find_record(workflow_id: str | None = None, uploaded_filename: str | None = None) -> dict[str, Any] | None:
    for record in list_profiles():
        if workflow_id and record.get("id") == workflow_id:
            return record
        if uploaded_filename and record.get("uploaded_filename") == uploaded_filename:
            return record
    return None


def _history(record: dict[str, Any] | None) -> list[dict[str, Any]]:
    return (record or {}).get("workflow_history") or []


def _current_stage(record: dict[str, Any] | None) -> str:
    history = _history(record)
    if history:
        metadata = history[-1].get("metadata") or {}
        return metadata.get("stage") or history[-1].get("status") or "queued"
    status = (record or {}).get("status") or "queued"
    return "resume_uploaded" if status == "uploaded" else status


def _retry_count(record: dict[str, Any] | None) -> int:
    return sum(
        1
        for event in _history(record)
        if (event.get("metadata") or {}).get("action") in {"retry", "restart"}
    )


def _last_failure_reason(record: dict[str, Any] | None) -> str | None:
    for event in reversed(_history(record)):
        metadata = event.get("metadata") or {}
        if event.get("status") == "failed":
            return metadata.get("reason") or metadata.get("failure_reason")
    return None


def can_transition(current_stage: str, next_stage: str) -> bool:
    return next_stage in ALLOWED_TRANSITIONS.get(current_stage, set())


def is_known_stage(stage: str) -> bool:
    return stage in STAGE_SEQUENCE


def _execution_metadata(
    stage: str,
    previous_stage: str,
    retry_count: int,
    failure_reason: str | None,
    lifecycle: str,
    worker_owner: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage_def = STAGE_DEFINITIONS.get(stage, {})
    metadata = normalize_event_metadata(
        event_type=stage_def.get("event_type", f"workflow.{stage}"),
        stage=stage,
        status=stage_def.get("status", stage),
        source="workflow-engine",
        owner=stage_def.get("owner", "workflow-engine"),
        severity=stage_def.get("severity", "info"),
        lifecycle=lifecycle,
        extra={
        "stage": stage,
        "label": stage_def.get("label", stage.replace("_", " ").title()),
        "progress": stage_def.get("progress", 0),
        "state": stage_def.get("state", "running"),
        "current_stage": stage,
        "previous_stage": previous_stage,
        "retry_count": retry_count,
        "failure_reason": failure_reason,
        "last_event": stage_def.get("event_type", f"workflow.{stage}"),
        "timeout_seconds": STAGE_TIMEOUTS.get(stage),
        "worker_owner": worker_owner,
        },
    )
    if extra:
        metadata.update(extra)
    return metadata


def _emit_stage_event(
    workflow_id: str,
    target_roles: list[str],
    stage: str,
    previous_stage: str,
    retry_count: int,
    failure_reason: str | None = None,
    lifecycle: str = "enter",
    worker_owner: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    stage_def = STAGE_DEFINITIONS[stage]
    update_profile(
        workflow_id,
        {
            "status": stage_def["status"],
            "target_roles": target_roles,
            "metadata": _execution_metadata(stage, previous_stage, retry_count, failure_reason, lifecycle, worker_owner, extra),
        },
    )


def record_failure(
    workflow_id: str,
    reason: str,
    stage: str | None = None,
    retry_count: int = 0,
    previous_stage: str | None = None,
) -> None:
    record = _find_record(workflow_id=workflow_id)
    if not record:
        return
    failed_stage = stage or _current_stage(record)
    prior_stage = previous_stage or failed_stage
    update_profile(
        workflow_id,
        {
            "status": "failed",
            "target_roles": record.get("target_roles") or [],
            "metadata": normalize_event_metadata(
                event_type=f"{failed_stage}.failed",
                stage=failed_stage,
                status="failed",
                source="workflow-engine",
                owner="workflow-engine",
                severity="error",
                lifecycle="failure",
                extra={
                    "label": f"{failed_stage.replace('_', ' ').title()} failed",
                    "progress": 100,
                    "state": "failed",
                    "reason": reason,
                    "failure_reason": reason,
                    "current_stage": failed_stage,
                    "previous_stage": prior_stage,
                    "retry_count": retry_count,
                    "last_event": f"{failed_stage}.failed",
                    "recovery_state": "recoverable",
                    "timeout_seconds": STAGE_TIMEOUTS.get(failed_stage),
                },
            ),
        },
    )


async def _load_resume_text(uploaded_filename: str | None, resume_text: str | None) -> str:
    if resume_text:
        return resume_text
    if not uploaded_filename:
        raise ValueError("No resume text available for analysis")
    candidate = Path(settings.upload_dir) / "resumes" / uploaded_filename
    if candidate.exists():
        return candidate.read_text(encoding="utf-8", errors="ignore")
    raise ValueError("No resume text available for analysis")


async def _existing_analysis(uploaded_filename: str | None) -> dict[str, Any] | None:
    if not uploaded_filename:
        return None
    for record in await asyncio.to_thread(list_profiles):
        if record.get("uploaded_filename") == uploaded_filename and isinstance(record.get("profile"), dict):
            parsed = record.get("profile") or {}
            return {
                "analysis_raw": record.get("analysis_raw") or "",
                "parsed": parsed,
                "ats_score": parsed.get("ats_score"),
                "role_compatibility": parsed.get("role_compatibility"),
            }
    return None


async def execute_workflow(
    uploaded_filename: str | None,
    resume_text: str | None,
    roles: list[str],
    start_stage: str = "processing",
    workflow_id: str | None = None,
    retry_count: int = 0,
    worker_owner: str | None = None,
) -> dict[str, Any]:
    from services.analysis_service import WorkflowCancelledError, WorkflowPausedError, analyze_text
    from services.workflow_runtime import get_runtime_state

    resume_text = await _load_resume_text(uploaded_filename, resume_text)
    record = await asyncio.to_thread(_find_record, workflow_id, uploaded_filename)
    if not record:
        raise ValueError("Workflow not found")

    workflow_id = record.get("id")
    current_stage = _current_stage(record)
    actual_retry_count = max(retry_count, _retry_count(record))
    failure_reason = _last_failure_reason(record)
    recovery_mode = "resume" if start_stage != "processing" else "standard"
    if actual_retry_count:
        recovery_mode = "retry"

    if not is_known_stage(start_stage):
        raise ValueError(f"Unknown workflow stage: {start_stage}")

    if not can_transition(current_stage, start_stage):
        raise ValueError(f"Invalid workflow transition: {current_stage} -> {start_stage}")

    def ensure_runtime_state(stage: str, previous_stage: str) -> None:
        runtime = get_runtime_state(uploaded_filename)
        if runtime.get("cancel_requested"):
            update_profile(
                workflow_id,
                {
                    "status": "cancelled",
                    "target_roles": roles,
                    "metadata": normalize_event_metadata(
                        event_type="workflow.cancelled",
                        stage="cancelled",
                        status="cancelled",
                        source="workflow-engine",
                        owner="workflow-engine",
                        severity="warning",
                        lifecycle="cancelled",
                        extra={
                            "label": f"Workflow cancelled during {stage}",
                            "progress": 100,
                            "state": "cancelled",
                            "reason": "Cancelled by user",
                            "failure_reason": failure_reason,
                            "current_stage": "cancelled",
                            "previous_stage": previous_stage,
                            "retry_count": actual_retry_count,
                            "last_event": "workflow.cancelled",
                            "recovery_state": "recoverable",
                            "worker_owner": worker_owner,
                        },
                    ),
                },
            )
            raise WorkflowCancelledError("Workflow cancelled by user")
        if runtime.get("pause_requested"):
            update_profile(
                workflow_id,
                {
                    "status": "paused",
                    "target_roles": roles,
                    "metadata": normalize_event_metadata(
                        event_type="workflow.paused",
                        stage="paused",
                        status="paused",
                        source="workflow-engine",
                        owner="workflow-engine",
                        severity="warning",
                        lifecycle="paused",
                        extra={
                            "label": f"Workflow paused before {stage.replace('_', ' ')}",
                            "progress": STAGE_DEFINITIONS.get(previous_stage, {}).get("progress", 35),
                            "state": "paused",
                            "reason": "Paused by user",
                            "current_stage": "paused",
                            "previous_stage": previous_stage,
                            "resume_stage": stage,
                            "checkpoint_stage": previous_stage,
                            "retry_count": actual_retry_count,
                            "last_event": "workflow.paused",
                            "recovery_state": "recoverable",
                            "worker_owner": worker_owner,
                        },
                    ),
                },
            )
            raise WorkflowPausedError("Workflow paused by user")

    stages_to_run = [stage for stage in STAGE_SEQUENCE if stage in STAGE_DEFINITIONS and STAGE_SEQUENCE.index(stage) >= STAGE_SEQUENCE.index(start_stage)]
    previous_stage = current_stage

    try:
        for stage in stages_to_run:
            if stage == "optimization_ready":
                break
            _emit_stage_event(
                workflow_id,
                roles,
                stage,
                previous_stage,
                actual_retry_count,
                failure_reason=failure_reason,
                lifecycle="retry" if recovery_mode == "retry" and stage == start_stage else "enter",
                worker_owner=worker_owner,
                extra={
                    "recovery_mode": recovery_mode,
                    "resume_supported": True,
                },
            )
            ensure_runtime_state(stage, previous_stage)
            previous_stage = stage

        if start_stage == "optimization_ready":
            analysis = await _existing_analysis(uploaded_filename) or await asyncio.wait_for(analyze_text(resume_text, roles), timeout=STAGE_TIMEOUTS["ats_analysis"])
        else:
            analysis = await asyncio.wait_for(analyze_text(resume_text, roles), timeout=STAGE_TIMEOUTS["ats_analysis"])

        ensure_runtime_state("ats_analysis", previous_stage)
        parsed = analysis.get("parsed") if isinstance(analysis, dict) else None
        final_metadata = _execution_metadata(
            "optimization_ready",
            previous_stage,
            actual_retry_count,
            failure_reason,
            "exit",
            worker_owner,
            {
                "role_count": len(roles),
                "ats_score": parsed.get("ats_score") if isinstance(parsed, dict) else None,
                "recovery_mode": recovery_mode,
                "resume_supported": True,
                "recovery_state": "stable",
            },
        )
        await asyncio.to_thread(
            update_profile,
            workflow_id,
            {
                "analysis_raw": analysis.get("analysis_raw"),
                "parsed": parsed,
                "target_roles": roles,
                "ats_score": parsed.get("ats_score") if isinstance(parsed, dict) else None,
                "status": "analyzed",
                "metadata": final_metadata,
            },
        )
        return analysis
    except WorkflowCancelledError:
        raise
    except asyncio.TimeoutError as exc:
        record_failure(
            workflow_id,
            "Stage execution timed out",
            stage="ats_analysis",
            retry_count=actual_retry_count,
            previous_stage=previous_stage,
        )
        raise RuntimeError("Workflow execution timed out") from exc
    except Exception as exc:
        record_failure(
            workflow_id,
            str(exc),
            stage=previous_stage if previous_stage in STAGE_DEFINITIONS else start_stage,
            retry_count=actual_retry_count,
            previous_stage=previous_stage,
        )
        raise


async def execute_workflow_task(task: dict[str, Any]) -> dict[str, Any]:
    return await execute_workflow(
        task.get("upload_id"),
        None,
        task.get("target_roles") or [],
        start_stage=task.get("retry_stage") or "processing",
        workflow_id=task.get("workflow_id"),
        retry_count=task.get("retry_count") or 0,
        worker_owner=task.get("worker_id"),
    )