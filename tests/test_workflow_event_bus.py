from services import workflow_event_bus


def test_build_snapshot_event_contains_stable_contract(monkeypatch):
    monkeypatch.setattr(
        workflow_event_bus,
        "_status_payload",
        lambda: {
            "profiles": [],
            "activity_feed": [],
            "overview": {"active": 0, "completed": 0, "failed": 0, "queued": 0, "total": 0},
            "queue": {"size": 0, "pending": []},
            "automation_placeholders": {},
            "transport": {"contract": "workflow-status-payload-v1", "mode": "sse-primary"},
        },
    )

    envelope = workflow_event_bus.build_snapshot_event()

    assert envelope["type"] == "workflow.event"
    assert envelope["event_type"] == "workflow.snapshot"
    assert envelope["contract"] == "workflow-status-payload-v1"
    assert envelope["event_contract"] == "workflow-event-envelope-v1"
    assert envelope["event_version"] == 1
    assert envelope["payload"]["transport"]["mode"] == "sse-primary"


def test_publish_event_reaches_subscriber(monkeypatch):
    monkeypatch.setattr(
        workflow_event_bus,
        "_status_payload",
        lambda: {
            "profiles": [],
            "activity_feed": [],
            "overview": {},
            "queue": {},
            "automation_placeholders": {},
            "transport": {"contract": "workflow-status-payload-v1"},
        },
    )
    subscriber_id, q = workflow_event_bus.subscribe()
    try:
        workflow_event_bus.publish_event("analysis.completed", workflow_id="wf-1", event={"stage": "ats_analysis"})
        envelope = q.get(timeout=1)
        assert envelope["workflow_id"] == "wf-1"
        assert envelope["event_type"] == "analysis.completed"
        assert envelope["event"]["metadata"]["contract"] == "workflow-metadata-v1"
    finally:
        workflow_event_bus.unsubscribe(subscriber_id)


def test_publish_event_respects_filters(monkeypatch):
    monkeypatch.setattr(
        workflow_event_bus,
        "_status_payload",
        lambda: {
            "profiles": [],
            "activity_feed": [],
            "overview": {},
            "queue": {},
            "automation_placeholders": {},
            "transport": {"contract": "workflow-status-payload-v1"},
        },
    )
    matching_id, matching_queue = workflow_event_bus.subscribe(workflow_id="wf-allowed", event_type="analysis.completed")
    other_id, other_queue = workflow_event_bus.subscribe(workflow_id="wf-other")
    try:
        workflow_event_bus.publish_event("analysis.completed", workflow_id="wf-allowed", source="workflow-engine")
        envelope = matching_queue.get(timeout=1)
        assert envelope["workflow_id"] == "wf-allowed"
        assert other_queue.empty()
    finally:
        workflow_event_bus.unsubscribe(matching_id)
        workflow_event_bus.unsubscribe(other_id)


def test_publish_event_respects_stage_severity_and_status_filters(monkeypatch):
    monkeypatch.setattr(
        workflow_event_bus,
        "_status_payload",
        lambda: {
            "profiles": [],
            "activity_feed": [],
            "overview": {},
            "queue": {},
            "automation_placeholders": {},
            "transport": {"contract": "workflow-status-payload-v1"},
        },
    )
    matching_id, matching_queue = workflow_event_bus.subscribe(stage="ats_analysis", severity="error", status="failed")
    other_id, other_queue = workflow_event_bus.subscribe(stage="processing")
    try:
        workflow_event_bus.publish_event(
            "analysis.failed",
            workflow_id="wf-ops",
            event={
                "stage": "ats_analysis",
                "status": "failed",
                "severity": "error",
            },
        )
        envelope = matching_queue.get(timeout=1)
        assert envelope["stage"] == "ats_analysis"
        assert envelope["severity"] == "error"
        assert envelope["status"] == "failed"
        assert other_queue.empty()
    finally:
        workflow_event_bus.unsubscribe(matching_id)
        workflow_event_bus.unsubscribe(other_id)