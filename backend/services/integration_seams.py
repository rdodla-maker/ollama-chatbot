"""Lightweight manifest for Stage 2 integration extension points."""

from __future__ import annotations

from typing import Any

from services.workflow_contracts import WORKFLOW_EVENT_CONTRACT, WORKFLOW_STATUS_CONTRACT


def build_integration_seams_payload() -> dict[str, dict[str, Any]]:
    return {
        "n8n": {
            "status": "ready",
            "integration_type": "event-consumer",
            "contract": WORKFLOW_EVENT_CONTRACT,
            "entrypoint": "workflow events",
        },
        "gmail": {
            "status": "planned",
            "integration_type": "notification-adapter",
            "contract": WORKFLOW_STATUS_CONTRACT,
            "entrypoint": "workflow status payload",
        },
        "linkedin": {
            "status": "planned",
            "integration_type": "outbound-automation-adapter",
            "contract": WORKFLOW_STATUS_CONTRACT,
            "entrypoint": "candidate intelligence snapshot",
        },
        "job_discovery": {
            "status": "planned",
            "integration_type": "inbound-workflow-trigger",
            "contract": WORKFLOW_EVENT_CONTRACT,
            "entrypoint": "workflow enqueue boundary",
        },
        "recruiter_automation": {
            "status": "planned",
            "integration_type": "action-orchestration-adapter",
            "contract": WORKFLOW_EVENT_CONTRACT,
            "entrypoint": "workflow action envelope",
        },
    }