import json

import pytest
from fastapi.testclient import TestClient
from sse_starlette import EventSourceResponse
from sse_starlette.event import ServerSentEvent

from backend.api import routes
from backend.main import app


client = TestClient(app)


def test_workflow_status_ok():
    resp = client.get("/workflow-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "profiles" in data
    assert isinstance(data["profiles"], list)
    assert "analytics" in data


@pytest.mark.anyio
async def test_workflow_events_query_ok(monkeypatch):
    monkeypatch.setattr(
        routes,
        "list_profiles",
        lambda: [
            {
                "id": "wf-query",
                "uploaded_filename": "resume.pdf",
                "workflow_history": [
                    {
                        "when": "2026-05-28T10:00:00",
                        "status": "failed",
                        "metadata": {"stage": "ats_analysis", "event_type": "analysis.failed", "severity": "error", "reason": "timeout"},
                    }
                ],
            }
        ],
    )

    result = await routes.workflow_events(severity="error", search="timeout")
    assert result["total"] == 1
    assert "aggregations" in result


@pytest.mark.anyio
async def test_resume_version_detail_route_returns_payload(monkeypatch):
    monkeypatch.setattr(
        routes,
        "get_resume_version_detail",
        lambda db, version_id: {
            "id": version_id,
            "comparison": {"added_lines": ["Leadership"], "removed_lines": []},
            "previous_version": {"id": "prev-1", "version_label": "Uploaded v1", "ats_score": 82},
        },
    )

    result = await routes.resume_version_detail_route("version-1")

    assert result["id"] == "version-1"
    assert result["comparison"]["added_lines"] == ["Leadership"]


@pytest.mark.anyio
async def test_workflow_status_stream_returns_sse_response(monkeypatch):
    async def fake_stream(*args, **kwargs):
        yield ServerSentEvent(
            data=json.dumps(
                {
                    "type": "workflow.event",
                    "event_type": "workflow.snapshot",
                    "payload": {"profiles": []},
                }
            ),
            event="workflow.snapshot",
        )

    monkeypatch.setattr(routes, "stream_workflow_events", fake_stream)

    class DummyRequest:
        async def is_disconnected(self):
            return False

    response = await routes.workflow_status_stream(DummyRequest())

    assert isinstance(response, EventSourceResponse)
    assert response.media_type == "text/event-stream"
