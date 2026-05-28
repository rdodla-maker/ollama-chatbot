from services.workflow_status_service import build_workflow_profile, build_workflow_status_payload


def test_build_workflow_profile_shapes_retry_failure_metadata():
    record = {
        "id": "wf-1",
        "uploaded_filename": "resume.pdf",
        "created_at": "2026-05-27T10:00:00",
        "updated_at": "2026-05-27T10:04:00",
        "status": "failed",
        "target_roles": ["Data Engineer"],
        "profile": {"ats_score": 81},
        "ats_score": 81,
        "candidate_profile": {"display_name": "Resume", "skills": ["Python"]},
        "candidate_memory": [{"memory_type": "ats_gaps"}],
        "resume_versions": [{"version_kind": "uploaded"}],
        "workflow_history": [
            {"when": "2026-05-27T10:00:00", "status": "uploaded", "metadata": {"label": "Resume uploaded", "stage": "resume_uploaded", "progress": 10, "state": "completed"}},
            {"when": "2026-05-27T10:01:00", "status": "retrying", "metadata": {"label": "Workflow retry queued", "stage": "retrying", "progress": 25, "state": "retrying", "action": "retry", "retry_count": 1}},
            {"when": "2026-05-27T10:04:00", "status": "failed", "metadata": {"label": "Workflow failed", "stage": "failed", "progress": 100, "state": "failed", "reason": "ollama timeout"}},
        ],
    }

    profile = build_workflow_profile(record)

    assert profile["retry_count"] == 1
    assert profile["failure_reason"] == "ollama timeout"
    assert profile["current_stage_state"] == "failed"
    assert any(item["action"] == "retry" and item["enabled"] for item in profile["available_actions"])
    assert profile["timeline"][1]["metadata"]["retry_count"] == 1
    assert profile["execution_metadata"]["current_stage"] == "failed"
    assert profile["execution_metadata"]["last_event"] == "failed"
    assert profile["candidate_profile"]["skills"] == ["Python"]
    assert profile["resume_versions"][0]["version_kind"] == "uploaded"


def test_build_workflow_status_payload_counts_processing_and_queue():
    payload = build_workflow_status_payload(
        [
            {
                "id": "wf-1",
                "uploaded_filename": "one.pdf",
                "created_at": "2026-05-27T10:00:00",
                "status": "processing",
                "target_roles": [],
                "profile": None,
                "ats_score": None,
                "workflow_history": [
                    {"when": "2026-05-27T10:00:00", "status": "processing", "metadata": {"stage": "processing", "label": "Workflow processing", "progress": 15, "state": "processing"}},
                ],
            },
            {
                "id": "wf-2",
                "uploaded_filename": "two.pdf",
                "created_at": "2026-05-27T10:00:00",
                "status": "queued",
                "target_roles": [],
                "profile": None,
                "ats_score": None,
                "workflow_history": [
                    {"when": "2026-05-27T10:00:00", "status": "queued", "metadata": {"stage": "queued", "label": "Workflow queued", "progress": 15, "state": "queued"}},
                ],
            },
        ],
        {"size": 1, "pending": [{"type": "analyze_resume"}]},
    )

    assert payload["overview"]["active"] == 1
    assert payload["overview"]["queued"] == 1
    assert payload["queue"]["size"] == 1
    assert payload["contracts"]["event_envelope"] == "workflow-event-envelope-v1"
    assert payload["integration_seams"]["n8n"]["status"] == "ready"
    assert payload["transport"]["contract"] == "workflow-status-payload-v1"
    assert "filters" in payload["transport"]
    assert "analytics" in payload
    assert "observability" in payload