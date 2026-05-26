"""API integration tests (no Ollama required for health)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert data.get("version") == "3.0.0"


def test_chat_missing_body():
    r = client.post("/chat", json={})
    assert r.status_code == 422


@patch("api.routes.generate_completion")
def test_chat_no_pdfs(mock_gen):
    mock_gen.return_value = "should not be called"
    with patch("api.routes.search_chunks_with_metadata", return_value=[]):
        r = client.post("/chat", json={"message": "hello"})
    assert r.status_code == 200
    assert "No PDF" in r.json()["response"]


@patch("api.routes.ask_agent")
def test_agent(mock_agent):
    mock_agent.return_value = {
        "reasoning": ["step 1"],
        "plan": "1. Do thing",
        "response": "Done.",
    }
    r = client.post("/agent", json={"message": "test"})
    assert r.status_code == 200
    data = r.json()
    assert data["response"] == "Done."
    assert data["reasoning"] == ["step 1"]
    assert data["plan"] == "1. Do thing"
