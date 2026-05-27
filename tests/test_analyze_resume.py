import asyncio
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_analyze_resume_structured(monkeypatch):
    async def fake_generate(prompt: str, stream: bool = False):
        return (
            '{"skills": ["Python", "SQL"], "ats_score": 78.5, '
            '"role_compatibility": {"Data Engineer": {"score": 85, "explanation": "Good match"}}}'
        )

    monkeypatch.setattr("services.ollama_service.generate_completion", fake_generate)

    payload = {"resume_text": "Experienced Python developer...", "target_roles": ["Data Engineer"]}
    resp = client.post("/analyze-resume", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis_raw" in data
    assert data.get("ats_score") == 78.5
    assert data.get("parsed") and data["parsed"]["skills"] == ["Python", "SQL"]
