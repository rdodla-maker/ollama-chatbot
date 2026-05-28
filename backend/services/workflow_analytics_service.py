"""Workflow analytics helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from services.observability_service import build_performance_drilldown


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


def build_workflow_analytics(records: list[dict[str, Any]]) -> dict[str, Any]:
    durations: list[float] = []
    retry_counts: list[int] = []
    ats_scores: list[float] = []
    stage_windows: dict[str, list[float]] = {}

    for record in records:
        history = record.get("workflow_history") or []
        if history:
            duration = _duration_seconds(history[0].get("when"), history[-1].get("when"))
            if duration is not None:
                durations.append(duration)
            for index, event in enumerate(history[:-1]):
                metadata = event.get("metadata") or {}
                stage = metadata.get("stage") or event.get("status") or "queued"
                window = _duration_seconds(event.get("when"), history[index + 1].get("when"))
                if window is not None:
                    stage_windows.setdefault(stage, []).append(window)
            retry_counts.append(
                sum(1 for event in history if (event.get("metadata") or {}).get("action") in {"retry", "restart", "resume"})
            )
        if record.get("ats_score") is not None:
            ats_scores.append(record["ats_score"])

    total = len(records)
    completed = sum(1 for record in records if record.get("status") in {"analyzed", "completed", "analysis_completed"})
    failed = sum(1 for record in records if record.get("status") == "failed")

    bottlenecks = [
        {
            "stage": stage,
            "average_duration_seconds": round(sum(values) / len(values), 2),
            "samples": len(values),
        }
        for stage, values in stage_windows.items()
        if values
    ]
    bottlenecks.sort(key=lambda item: item["average_duration_seconds"], reverse=True)

    return {
        "workflow_success_rate": round((completed / total) * 100, 2) if total else 0,
        "average_execution_seconds": round(sum(durations) / len(durations), 2) if durations else 0,
        "retry_statistics": {
            "total_retries": sum(retry_counts),
            "workflows_with_retries": sum(1 for value in retry_counts if value),
            "average_retries": round(sum(retry_counts) / len(retry_counts), 2) if retry_counts else 0,
        },
        "stage_bottlenecks": bottlenecks[:5],
        "ats_score_trends": {
            "average": round(sum(ats_scores) / len(ats_scores), 2) if ats_scores else None,
            "best": max(ats_scores) if ats_scores else None,
            "worst": min(ats_scores) if ats_scores else None,
            "latest": ats_scores[-1] if ats_scores else None,
        },
        "workflow_counts": {
            "total": total,
            "completed": completed,
            "failed": failed,
        },
        "performance": build_performance_drilldown(records),
    }