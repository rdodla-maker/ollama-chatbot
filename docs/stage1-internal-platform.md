# Stage 1 Internal Platform

This document freezes the internal platform boundaries at the end of Stage 1 so Stage 2 external automation work can attach to stable seams instead of implementation details.

## Architecture Overview

The platform remains a FastAPI backend with a React mission-control frontend, an in-memory workflow worker, SSE transport, SQLite persistence, and additive workflow intelligence services.

Core runtime flow:

1. Resume upload creates a persisted workflow profile and publishes `workflow.created`.
2. The task queue enqueues `analyze_resume` work and publishes `workflow.queued`.
3. The workflow execution engine advances valid stages only.
4. Repository persistence appends workflow history and publishes workflow events.
5. The SSE stream service emits stable workflow envelopes plus filtered status payload snapshots.
6. The React dashboard consumes status payloads and version-detail APIs for operations, diagnostics, and rollback preview.

## Workflow Lifecycle

Stable execution stages:

1. `queued`
2. `processing`
3. `parsing_started`
4. `skills_extracted`
5. `ats_analysis`
6. `optimization_ready`

Stable terminal states:

1. `failed`
2. `cancelled`

Operational control states:

1. `retrying`
2. `paused`

Hardening rules:

1. Invalid transitions are rejected in the execution engine.
2. Unknown retry or resume stages are rejected in orchestration.
3. Timeout failures are normalized into workflow failure events.
4. Pause and cancel states preserve checkpoint metadata for recovery.
5. New optimized resume versions are created only when the snapshot actually changes.

## Contract Layer

The internal workflow contracts are centralized in `backend/services/workflow_contracts.py`.

Frozen contract identifiers:

1. Status payload: `workflow-status-payload-v1`
2. Event envelope: `workflow-event-envelope-v1`
3. Metadata payload: `workflow-metadata-v1`

Stable transport capabilities:

1. Primary mode: `sse-primary`
2. Supported transports: `polling`, `sse`, `websocket-ready`, `multi-client-ready`
3. Stable filters: `workflow_id`, `stage`, `severity`, `event_type`, `status`, `source`, `from_date`, `to_date`
4. Stable recovery actions: `retry`, `resume`, `restart`

Event envelope fields:

1. `type`
2. `contract`
3. `event_contract`
4. `event_version`
5. `sequence`
6. `timestamp`
7. `event_type`
8. `workflow_id`
9. `source`
10. `stage`
11. `status`
12. `severity`
13. `event`
14. `payload`

Workflow metadata conventions:

1. `source` identifies the emitting service boundary.
2. `owner` identifies the owning runtime component.
3. `severity` is normalized to `info`, `warning`, or `error`.
4. `contract` and `metadata_version` travel with workflow metadata.
5. `lifecycle` identifies whether the event is `created`, `enter`, `retry`, `resume`, `paused`, `cancelled`, or `failure`.

## Service Ownership

Service ownership is intentionally narrow:

1. `workflow_execution_service.py`: stage transitions, timeout handling, lifecycle emission, failure recording.
2. `workflow_orchestration_service.py`: user actions, retry validation, pause/resume/cancel/restart routing.
3. `workflow_event_bus.py`: stable event envelopes and subscriber filtering.
4. `workflow_stream_service.py`: SSE transport and filtered payload streaming.
5. `workflow_status_service.py`: mission-control response shaping.
6. `workflow_analytics_service.py`: aggregate workflow analytics and performance summaries.
7. `observability_service.py`: failure diagnostics, workflow audit, orchestration and worker visibility.
8. `candidate_intelligence_service.py`: candidate memory, resume versioning, and rollback comparison data.
9. `repository.py`: SQLite persistence seam plus event publication after state changes.

## Integration Seams

Stage 2 integrations should attach only through explicit seams surfaced by `backend/services/integration_seams.py`.

Prepared seams:

1. `n8n`: consume workflow event envelopes.
2. `gmail`: consume stable workflow status and candidate intelligence snapshots.
3. `linkedin`: consume outbound automation-ready workflow and candidate state.
4. `job_discovery`: trigger new internal workflows through the enqueue boundary.
5. `recruiter_automation`: consume workflow action and audit events.

Non-goals for Stage 1:

1. No direct Gmail integration.
2. No LinkedIn automation.
3. No scraping or recruiter outreach implementation.
4. No external queue or orchestration platform implementation.

## Operational Guidance

Recommended validation before Stage 2 work:

1. Run the workflow backend suite with `PYTHONPATH` set to `backend`.
2. Build the frontend with `npm run build`.
3. Smoke test `workflow-status`, `workflow-events`, `workflow-status/stream`, and resume version detail endpoints with the backend running.
4. Confirm the mission-control dashboard still renders event explorer, rollback preview, diagnostics, analytics, and audit views.