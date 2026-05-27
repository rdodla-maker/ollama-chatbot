from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_workflow_status_ok():
    resp = client.get("/workflow-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "profiles" in data
    assert isinstance(data["profiles"], list)
