from services import workflow_orchestration_service as orchestration


def test_apply_retry_updates_state_and_enqueues(monkeypatch):
    record = {
        "id": "wf-1",
        "uploaded_filename": "resume.pdf",
        "status": "failed",
        "target_roles": ["Platform Engineer"],
        "workflow_history": [
            {"when": "2026-05-27T10:00:00", "status": "failed", "metadata": {"reason": "network"}},
        ],
    }
    updates = []
    tasks = []

    monkeypatch.setattr(orchestration, "list_profiles", lambda: [record])
    monkeypatch.setattr(orchestration, "update_profile", lambda workflow_id, payload: updates.append((workflow_id, payload)) or {})
    monkeypatch.setattr(orchestration, "clear_cancel", lambda upload_id: None)

    def fake_enqueue(task):
        tasks.append(task)

    monkeypatch.setattr("services.task_queue.enqueue_task", fake_enqueue)

    result = orchestration.apply_workflow_action("wf-1", "retry")

    assert result["status"] == "queued"
    assert updates[0][1]["status"] == "retrying"
    assert updates[0][1]["metadata"]["retry_count"] == 1
    assert tasks[0]["workflow_id"] == "wf-1"


def test_apply_stage_retry_targets_specific_stage(monkeypatch):
    record = {
        "id": "wf-stage",
        "uploaded_filename": "resume-stage.pdf",
        "status": "failed",
        "target_roles": ["ML Engineer"],
        "workflow_history": [
            {"when": "2026-05-27T10:00:00", "status": "failed", "metadata": {"reason": "parser failure"}},
        ],
    }
    tasks = []

    monkeypatch.setattr(orchestration, "list_profiles", lambda: [record])
    monkeypatch.setattr(orchestration, "update_profile", lambda workflow_id, payload: {})
    monkeypatch.setattr(orchestration, "clear_cancel", lambda upload_id: None)
    monkeypatch.setattr("services.task_queue.enqueue_task", lambda task: tasks.append(task))

    result = orchestration.apply_workflow_action("wf-stage", "retry", "optimization_ready")

    assert result["stage"] == "optimization_ready"
    assert tasks[0]["retry_stage"] == "optimization_ready"


def test_apply_cancel_requests_cancel_and_marks_cancelled(monkeypatch):
    record = {
        "id": "wf-2",
        "uploaded_filename": "resume-2.pdf",
        "status": "processing",
        "target_roles": [],
        "workflow_history": [],
    }
    updates = []
    cancelled = []

    monkeypatch.setattr(orchestration, "list_profiles", lambda: [record])
    monkeypatch.setattr(orchestration, "update_profile", lambda workflow_id, payload: updates.append((workflow_id, payload)) or {})
    monkeypatch.setattr(orchestration, "request_cancel", lambda upload_id: cancelled.append(upload_id))
    monkeypatch.setattr("services.task_queue.cancel_queued_workflow", lambda workflow_id, upload_id: False)

    result = orchestration.apply_workflow_action("wf-2", "cancel")

    assert result["status"] == "cancelled"
    assert cancelled == ["resume-2.pdf"]
    assert updates[0][1]["status"] == "cancelled"
    assert updates[0][1]["metadata"]["state"] == "cancelled"


def test_available_actions_disable_retry_after_limit():
    record = {
        "id": "wf-3",
        "uploaded_filename": "resume-3.pdf",
        "status": "failed",
        "target_roles": [],
        "workflow_history": [
            {"when": "2026-05-27T10:00:00", "status": "retrying", "metadata": {"action": "retry", "retry_count": 1}},
            {"when": "2026-05-27T10:01:00", "status": "retrying", "metadata": {"action": "retry", "retry_count": 2}},
            {"when": "2026-05-27T10:02:00", "status": "retrying", "metadata": {"action": "restart", "retry_count": 3}},
        ],
    }

    actions = orchestration.get_available_actions(record)
    retry_action = next(item for item in actions if item["action"] == "retry")
    restart_action = next(item for item in actions if item["action"] == "restart")

    assert retry_action["enabled"] is False
    assert restart_action["enabled"] is False


def test_stage_retry_actions_available_after_failure():
    record = {
        "id": "wf-4",
        "uploaded_filename": "resume-4.pdf",
        "status": "failed",
        "target_roles": [],
        "workflow_history": [],
    }

    actions = orchestration.get_stage_retry_actions(record)

    assert len(actions) == 3
    assert all(item["enabled"] for item in actions)


def test_apply_pause_marks_checkpoint(monkeypatch):
    record = {
        "id": "wf-pause",
        "uploaded_filename": "resume-pause.pdf",
        "status": "processing",
        "target_roles": ["Product Engineer"],
        "workflow_history": [
            {"when": "2026-05-28T10:00:00", "status": "processing", "metadata": {"stage": "processing"}},
        ],
    }
    updates = []
    pauses = []

    monkeypatch.setattr(orchestration, "list_profiles", lambda: [record])
    monkeypatch.setattr(orchestration, "update_profile", lambda workflow_id, payload: updates.append((workflow_id, payload)) or {})
    monkeypatch.setattr(orchestration, "request_pause", lambda upload_id: pauses.append(upload_id))
    monkeypatch.setattr("services.task_queue.cancel_queued_workflow", lambda workflow_id, upload_id: False)

    result = orchestration.apply_workflow_action("wf-pause", "pause")

    assert result["status"] == "paused"
    assert pauses == ["resume-pause.pdf"]
    assert updates[0][1]["metadata"]["resume_stage"] == "processing"


def test_apply_resume_enqueues_from_checkpoint(monkeypatch):
    record = {
        "id": "wf-resume",
        "uploaded_filename": "resume-resume.pdf",
        "status": "paused",
        "target_roles": ["ML Engineer"],
        "workflow_history": [
            {
                "when": "2026-05-28T10:00:00",
                "status": "paused",
                "metadata": {"stage": "paused", "resume_stage": "ats_analysis"},
            },
        ],
    }
    updates = []
    tasks = []
    cleared = []

    monkeypatch.setattr(orchestration, "list_profiles", lambda: [record])
    monkeypatch.setattr(orchestration, "update_profile", lambda workflow_id, payload: updates.append((workflow_id, payload)) or {})
    monkeypatch.setattr(orchestration, "clear_pause", lambda upload_id: cleared.append(upload_id))
    monkeypatch.setattr("services.task_queue.enqueue_task", lambda task: tasks.append(task))

    result = orchestration.apply_workflow_action("wf-resume", "resume")

    assert result["status"] == "queued"
    assert cleared == ["resume-resume.pdf"]
    assert tasks[0]["retry_stage"] == "ats_analysis"
    assert updates[0][1]["metadata"]["event_type"] == "workflow.resumed"


def test_apply_retry_rejects_unsupported_stage(monkeypatch):
    record = {
        "id": "wf-invalid-stage",
        "uploaded_filename": "resume-invalid.pdf",
        "status": "failed",
        "target_roles": [],
        "workflow_history": [
            {"when": "2026-05-27T10:00:00", "status": "failed", "metadata": {"reason": "network"}},
        ],
    }

    monkeypatch.setattr(orchestration, "list_profiles", lambda: [record])

    try:
        orchestration.apply_workflow_action("wf-invalid-stage", "retry", "queued")
        assert False, "Expected invalid retry stage to be rejected"
    except ValueError as exc:
        assert "Retry stage is not supported" in str(exc)