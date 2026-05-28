import pytest

from services import analysis_service, workflow_execution_service as execution_service


def test_can_transition_prevents_invalid_regression():
    assert execution_service.can_transition("queued", "processing") is True
    assert execution_service.can_transition("optimization_ready", "parsing_started") is False
    assert execution_service.can_transition("failed", "parsing_started") is True


@pytest.mark.anyio
async def test_execute_workflow_emits_lifecycle_metadata(monkeypatch):
    record = {
        "id": "wf-1",
        "uploaded_filename": "resume.pdf",
        "status": "uploaded",
        "target_roles": ["Platform Engineer"],
        "workflow_history": [
            {
                "when": "2026-05-28T10:00:00",
                "status": "uploaded",
                "metadata": {"stage": "resume_uploaded", "event_type": "workflow.created"},
            }
        ],
    }
    updates = []

    async def fake_analyze_text(_resume_text, _roles):
        return {
            "analysis_raw": "{}",
            "parsed": {"ats_score": 88, "role_compatibility": {"Platform Engineer": {"score": 90}}},
        }

    monkeypatch.setattr(execution_service, "list_profiles", lambda: [record])
    monkeypatch.setattr(execution_service, "update_profile", lambda workflow_id, payload: updates.append((workflow_id, payload)) or {})
    monkeypatch.setattr(analysis_service, "analyze_text", fake_analyze_text)
    monkeypatch.setattr("services.workflow_runtime.get_runtime_state", lambda _upload_id: {"cancel_requested": False})

    result = await execution_service.execute_workflow(
        uploaded_filename="resume.pdf",
        resume_text="resume body",
        roles=["Platform Engineer"],
        start_stage="processing",
        workflow_id="wf-1",
    )

    assert result["parsed"]["ats_score"] == 88
    assert [payload["status"] for _, payload in updates] == [
        "processing",
        "parsing_started",
        "skills_extracted",
        "analysis_started",
        "analyzed",
    ]
    assert updates[0][1]["metadata"]["previous_stage"] == "resume_uploaded"
    assert updates[-1][1]["metadata"]["stage"] == "optimization_ready"
    assert updates[-1][1]["metadata"]["previous_stage"] == "ats_analysis"
    assert updates[-1][1]["metadata"]["last_event"] == "optimization.completed"


@pytest.mark.anyio
async def test_execute_workflow_rejects_invalid_transition(monkeypatch):
    record = {
        "id": "wf-2",
        "uploaded_filename": "resume-2.pdf",
        "status": "analyzed",
        "target_roles": [],
        "workflow_history": [
            {
                "when": "2026-05-28T10:00:00",
                "status": "analyzed",
                "metadata": {"stage": "optimization_ready", "event_type": "optimization.completed"},
            }
        ],
    }

    monkeypatch.setattr(execution_service, "list_profiles", lambda: [record])

    with pytest.raises(ValueError, match="Invalid workflow transition"):
        await execution_service.execute_workflow(
            uploaded_filename="resume-2.pdf",
            resume_text="resume body",
            roles=[],
            start_stage="parsing_started",
            workflow_id="wf-2",
        )


@pytest.mark.anyio
async def test_execute_workflow_rejects_unknown_stage(monkeypatch):
    record = {
        "id": "wf-3",
        "uploaded_filename": "resume-3.pdf",
        "status": "uploaded",
        "target_roles": [],
        "workflow_history": [],
    }

    monkeypatch.setattr(execution_service, "list_profiles", lambda: [record])

    with pytest.raises(ValueError, match="Unknown workflow stage"):
        await execution_service.execute_workflow(
            uploaded_filename="resume-3.pdf",
            resume_text="resume body",
            roles=[],
            start_stage="bogus_stage",
            workflow_id="wf-3",
        )