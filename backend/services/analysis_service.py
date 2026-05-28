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


class WorkflowPausedError(RuntimeError):
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
    from services.workflow_execution_service import execute_workflow

    return await execute_workflow(
        uploaded_filename,
        resume_text,
        roles,
        start_stage=start_stage,
    )
