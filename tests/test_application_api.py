import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@patch("api.routes.generate_application_materials")
@patch("api.routes.append_application_to_sheet")
@patch("api.routes.append_application_record")
def test_generate_application(mock_record, mock_sheet, mock_generate):
    mock_generate.return_value = {
        "generated_email": "Email text",
        "generated_cover_letter": "Cover letter text",
        "resume_suggestions": "- Improve bullets",
    }
    mock_record.return_value = {
        "company": "Acme",
        "role": "Engineer",
        "application_date": "2026-05-26",
        "status": "pending",
        "generated_email": "Email text",
        "generated_cover_letter": "Cover letter text",
    }
    mock_sheet.return_value = {"saved": False, "message": "not configured"}

    response = client.post(
        "/generate-application",
        json={
            "company": "Acme",
            "role": "Engineer",
            "job_description": "We need a Python engineer who can build APIs and work with AI systems.",
            "skills": "Python, FastAPI, React",
            "resume_text": "Built internal tools and APIs for automation and productivity improvements.",
            "tone": "professional",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["generated_email"] == "Email text"
    assert data["generated_cover_letter"] == "Cover letter text"
    assert data["resume_suggestions"] == "- Improve bullets"


@patch("api.routes.list_application_records")
def test_application_tracker(mock_list):
    mock_list.return_value = [
        {
            "company": "Acme",
            "role": "Engineer",
            "application_date": "2026-05-26",
            "status": "pending",
            "generated_email": "Email text",
            "generated_cover_letter": "Cover letter text",
        }
    ]

    response = client.get("/application-tracker")

    assert response.status_code == 200
    data = response.json()
    assert len(data["applications"]) == 1
    assert data["applications"][0]["company"] == "Acme"