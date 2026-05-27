"""Shared AI analysis service used by endpoints and background workers.

Provides functions to analyze resume text using Ollama and return structured JSON.
"""
import json
import logging
import asyncio
from typing import Any, Dict
from services import ollama_service
from services.profile_store import update_profile, list_profiles
from services.workflow import add_event_by_filename, normalize_event_metadata
from pathlib import Path
from core.config import settings

logger = logging.getLogger("analysis")


class WorkflowCancelledError(RuntimeError):
    pass


def _build_prompt(resume_text: str, roles: list[str]) -> str:
    return (
        "You are an expert recruiter and resume analyst. Given a candidate resume and target roles, produce a single valid JSON object with the following keys:\n"
        "skills, projects, education, certifications, experience, strengths, missing_skills, role_compatibility, ats_score, recommendations\n"
        "role_compatibility should be a mapping of role-> {score: 0-100, explanation: str}. ats_score should be numeric 0-100. Output ONLY valid JSON.\n\n"
        f"TARGET_ROLES: {roles}\n\nRESUME:\n{resume_text[:12000]}\n\n"
    )


async def analyze_text(resume_text: str, roles: list[str]) -> Dict[str, Any]:
    prompt = _build_prompt(resume_text, roles)
    ai_response = await ollama_service.generate_completion(prompt)
    parsed = None
    try:
        parsed = json.loads(ai_response)
    except Exception:
        logger.exception("AI response was not valid JSON")
        parsed = None

    result = {
        "analysis_raw": ai_response,
        "parsed": parsed,
    }
    if isinstance(parsed, dict):
        result["ats_score"] = parsed.get("ats_score")
        result["role_compatibility"] = parsed.get("role_compatibility")
    return result


async def analyze_and_persist(
    uploaded_filename: str | None,
    resume_text: str | None,
    roles: list[str],
    start_stage: str = "processing",
) -> Dict[str, Any]:
    """Analyze given resume text (or load from upload) and persist analysis into profile store.

    Returns the structured analysis dict.
    """
    # load text if not provided
    if not resume_text and uploaded_filename:
        candidate = Path(settings.upload_dir) / "resumes" / uploaded_filename
        if candidate.exists():
            resume_text = candidate.read_text(encoding="utf-8", errors="ignore")

    if not resume_text:
        raise ValueError("No resume text available for analysis")

    from services.workflow_runtime import get_runtime_state

    def ensure_not_cancelled(stage: str) -> None:
        runtime = get_runtime_state(uploaded_filename)
        if runtime.get("cancel_requested"):
            if uploaded_filename:
                add_event_by_filename(
                    uploaded_filename,
                    "cancelled",
                    {
                        "stage": "cancelled",
                        "label": f"Workflow cancelled during {stage}",
                        "progress": 100,
                        "state": "cancelled",
                        "reason": "Cancelled by user",
                        "source": "workflow-engine",
                    },
                )
            raise WorkflowCancelledError("Workflow cancelled by user")

    stage_order = ["processing", "parsing_started", "skills_extracted", "ats_analysis", "optimization_ready"]
    start_index = stage_order.index(start_stage) if start_stage in stage_order else 0

    async def existing_analysis() -> Dict[str, Any] | None:
        records = await asyncio.to_thread(list_profiles)
        for record in records:
            if record.get("uploaded_filename") == uploaded_filename and isinstance(record.get("profile"), dict):
                parsed = record.get("profile") or {}
                return {
                    "analysis_raw": record.get("analysis_raw") or json.dumps(parsed),
                    "parsed": parsed,
                    "ats_score": parsed.get("ats_score"),
                    "role_compatibility": parsed.get("role_compatibility"),
                }
        return None

    if uploaded_filename:
        if start_index <= 0:
            add_event_by_filename(
                uploaded_filename,
                "processing",
                {
                    "stage": "processing",
                    "label": "Workflow processing",
                    "progress": 15,
                    "state": "processing",
                    "source": "workflow-engine",
                },
            )
            ensure_not_cancelled("startup")
        if start_index <= 1:
            add_event_by_filename(
                uploaded_filename,
                "parsing_started",
                {
                    "stage": "parsing_started",
                    "label": "Parsing started",
                    "progress": 20,
                    "state": "running",
                    "source": "workflow-engine",
                },
            )
            ensure_not_cancelled("parsing")
        if start_index <= 2:
            add_event_by_filename(
                uploaded_filename,
                "skills_extracted",
                {
                    "stage": "skills_extracted",
                    "label": "Skills extracted",
                    "progress": 45,
                    "state": "completed",
                    "source": "workflow-engine",
                    "event_type": "parsing.completed",
                },
            )
            ensure_not_cancelled("skills extraction")
        if start_index <= 3:
            add_event_by_filename(
                uploaded_filename,
                "analysis_started",
                {
                    "stage": "ats_analysis",
                    "label": "ATS analysis started",
                    "progress": 60,
                    "state": "running",
                    "source": "workflow-engine",
                },
            )
            ensure_not_cancelled("analysis")

    if start_stage == "optimization_ready":
        analysis = await existing_analysis() or await analyze_text(resume_text, roles)
    else:
        analysis = await analyze_text(resume_text, roles)
    ensure_not_cancelled("post-analysis")
    # build profile_obj
    profile_obj = {
        "analysis_raw": analysis.get("analysis_raw"),
        "parsed": analysis.get("parsed"),
        "target_roles": roles,
        "ats_score": None,
        "status": "analyzed",
    }
    parsed = analysis.get("parsed")
    if isinstance(parsed, dict):
        profile_obj["ats_score"] = parsed.get("ats_score")
        profile_obj["metadata"] = {
            "stage": "optimization_ready",
            "label": "Optimization ready",
            "progress": 100,
            "state": "completed",
            "role_count": len(roles),
            "ats_score": parsed.get("ats_score"),
            "source": "workflow-engine",
            "event_type": "optimization.completed",
        }
    else:
        profile_obj["metadata"] = {
            "stage": "analysis_completed",
            "label": "Analysis completed",
            "progress": 90,
            "state": "completed",
            "role_count": len(roles),
            "source": "workflow-engine",
            "event_type": "analysis.completed",
        }

    # persist via profile_store adapter
    try:
        # find profile by uploaded filename via list_profiles (sync adapter)
        records = await asyncio.to_thread(list_profiles)
        profile_id = None
        for r in records:
            if r.get("uploaded_filename") == uploaded_filename:
                profile_id = r.get("id")
                break
        if profile_id:
            await asyncio.to_thread(update_profile, profile_id, profile_obj)
    except Exception:
        logger.exception("Failed to persist analysis to profile store")

    if uploaded_filename:
        add_event_by_filename(
            uploaded_filename,
            "analysis_completed",
            {
                "stage": "optimization_ready",
                "label": "Optimization ready",
                "progress": 100,
                "state": "completed",
                "role_count": len(roles),
                "ats_score": profile_obj.get("ats_score"),
                "source": "workflow-engine",
                "event_type": "optimization.completed",
            },
        )
    return analysis
