"""Shared workflow transport and event contract helpers."""

from __future__ import annotations

from typing import Any

WORKFLOW_STATUS_CONTRACT = "workflow-status-payload-v1"
WORKFLOW_EVENT_CONTRACT = "workflow-event-envelope-v1"
WORKFLOW_METADATA_CONTRACT = "workflow-metadata-v1"
WORKFLOW_EVENT_VERSION = 1
WORKFLOW_METADATA_VERSION = 1
DEFAULT_WORKFLOW_SOURCE = "workflow-engine"
KNOWN_SEVERITIES = {"info", "warning", "error"}
SUPPORTED_TRANSPORTS = ["polling", "sse", "websocket-ready", "multi-client-ready"]
SUPPORTED_FILTERS = ["workflow_id", "stage", "severity", "event_type", "status", "source", "from_date", "to_date"]
RECOVERY_ACTIONS = ["retry", "resume", "restart"]


def normalize_source(source: str | None) -> str:
    value = (source or "").strip()
    return value or DEFAULT_WORKFLOW_SOURCE


def infer_event_severity(event_type: str | None, explicit: str | None = None, status: str | None = None) -> str:
    if explicit in KNOWN_SEVERITIES:
        return explicit
    if status == "failed" or (event_type or "").endswith(".failed"):
        return "error"
    if status in {"paused", "cancelled"} or event_type in {"workflow.cancelled", "workflow.paused", "heartbeat"}:
        return "warning"
    return "info"


def normalize_event_metadata(
    metadata: dict[str, Any] | None = None,
    *,
    event_type: str | None = None,
    stage: str | None = None,
    status: str | None = None,
    source: str | None = None,
    owner: str | None = None,
    severity: str | None = None,
    lifecycle: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = dict(metadata or {})
    normalized_source = normalize_source(normalized.get("source") or source)
    normalized_event_type = normalized.get("event_type") or event_type or status or "workflow.event"
    normalized_status = normalized.get("status") or status
    normalized_stage = normalized.get("stage") or stage
    normalized_owner = normalized.get("owner") or owner or normalized_source

    normalized.update(
        {
            "source": normalized_source,
            "owner": normalized_owner,
            "event_type": normalized_event_type,
            "severity": infer_event_severity(normalized_event_type, normalized.get("severity") or severity, normalized_status),
            "contract": WORKFLOW_METADATA_CONTRACT,
            "metadata_version": WORKFLOW_METADATA_VERSION,
            "lifecycle": normalized.get("lifecycle") or lifecycle or "event",
        }
    )
    if normalized_stage is not None:
        normalized["stage"] = normalized_stage
    if normalized_status is not None:
        normalized["status"] = normalized_status
    if extra:
        normalized.update(extra)
    return normalized


def build_contract_manifest() -> dict[str, Any]:
    return {
        "status_payload": WORKFLOW_STATUS_CONTRACT,
        "event_envelope": WORKFLOW_EVENT_CONTRACT,
        "event_version": WORKFLOW_EVENT_VERSION,
        "metadata": WORKFLOW_METADATA_CONTRACT,
        "metadata_version": WORKFLOW_METADATA_VERSION,
    }


def build_transport_capabilities() -> dict[str, Any]:
    return {
        "mode": "sse-primary",
        "supported": SUPPORTED_TRANSPORTS,
        "contract": WORKFLOW_STATUS_CONTRACT,
        "event_contract": WORKFLOW_EVENT_CONTRACT,
        "event_version": WORKFLOW_EVENT_VERSION,
        "metadata_contract": WORKFLOW_METADATA_CONTRACT,
        "metadata_version": WORKFLOW_METADATA_VERSION,
        "filters": SUPPORTED_FILTERS,
        "recovery": RECOVERY_ACTIONS,
    }