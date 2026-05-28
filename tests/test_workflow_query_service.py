from services.workflow_query_service import filter_workflow_records, search_workflow_events


def test_filter_workflow_records_by_current_stage_and_status():
    records = [
        {
            "id": "wf-1",
            "uploaded_filename": "one.pdf",
            "status": "paused",
            "target_roles": [],
            "workflow_history": [
                {"when": "2026-05-28T10:00:00", "status": "paused", "metadata": {"stage": "paused", "severity": "warning", "event_type": "workflow.paused"}},
            ],
        },
        {
            "id": "wf-2",
            "uploaded_filename": "two.pdf",
            "status": "analyzed",
            "target_roles": [],
            "workflow_history": [
                {"when": "2026-05-28T10:00:00", "status": "analysis_completed", "metadata": {"stage": "optimization_ready", "severity": "info", "event_type": "optimization.completed"}},
            ],
        },
    ]

    filtered = filter_workflow_records(records, {"stage": "paused", "status": "paused"})

    assert [record["id"] for record in filtered] == ["wf-1"]


def test_search_workflow_events_matches_text_and_filters():
    records = [
        {
            "id": "wf-ops",
            "uploaded_filename": "resume.pdf",
            "workflow_history": [
                {
                    "when": "2026-05-28T10:00:00",
                    "status": "failed",
                    "metadata": {
                        "stage": "ats_analysis",
                        "label": "ATS analysis failed",
                        "severity": "error",
                        "event_type": "analysis.failed",
                        "reason": "timeout",
                    },
                }
            ],
        }
    ]

    result = search_workflow_events(records, {"severity": "error", "search": "timeout"})

    assert result["total"] == 1
    assert result["results"][0]["event_type"] == "analysis.failed"


def test_search_workflow_events_supports_pagination_dates_and_aggregations():
    records = [
        {
            "id": "wf-1",
            "uploaded_filename": "resume-one.pdf",
            "workflow_history": [
                {
                    "when": "2026-05-28T10:00:00",
                    "status": "processing",
                    "metadata": {
                        "stage": "parsing_started",
                        "severity": "info",
                        "event_type": "parsing.started",
                    },
                },
                {
                    "when": "2026-05-28T10:05:00",
                    "status": "failed",
                    "metadata": {
                        "stage": "ats_analysis",
                        "severity": "error",
                        "event_type": "analysis.failed",
                        "reason": "timeout",
                    },
                },
            ],
        },
        {
            "id": "wf-2",
            "uploaded_filename": "resume-two.pdf",
            "workflow_history": [
                {
                    "when": "2026-05-29T10:00:00",
                    "status": "processing",
                    "metadata": {
                        "stage": "optimization_ready",
                        "severity": "warning",
                        "event_type": "optimization.completed",
                    },
                }
            ],
        },
    ]

    result = search_workflow_events(
        records,
        {"from_date": "2026-05-28T10:01:00", "to_date": "2026-05-29T11:00:00"},
        limit=1,
        page=2,
    )

    assert result["total"] == 2
    assert result["page"] == 2
    assert result["pages"] == 2
    assert len(result["results"]) == 1
    assert result["aggregations"]["severity"][0]["key"] in {"error", "warning"}