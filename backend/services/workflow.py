"""Workflow history and state helpers."""
from datetime import datetime
import json
from typing import Any, Dict
from services.repository import get_profile_by_filename
from services.repository import update_profile_db
from db import SessionLocal
import logging

logger = logging.getLogger("workflow")


def _now_iso():
    return datetime.utcnow().isoformat()


def normalize_event_metadata(status: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    meta = dict(metadata or {})
    meta.setdefault("source", "workflow-engine")
    meta.setdefault("event_type", _event_type_for(status, meta))
    return meta


def _event_type_for(status: str, metadata: Dict[str, Any]) -> str:
    stage = metadata.get("stage") or status
    explicit = metadata.get("event_type")
    if explicit:
        return explicit
    if status == "uploaded":
        return "workflow.created"
    if status == "processing":
        return "workflow.processing"
    if stage == "parsing_started":
        return "parsing.started"
    if stage == "skills_extracted":
        return "parsing.completed"
    if stage == "ats_analysis" and status == "analysis_started":
        return "analysis.started"
    if stage == "optimization_ready" and status in {"analysis_completed", "analyzed"}:
        return "optimization.completed"
    if stage == "analysis_completed":
        return "analysis.completed"
    if status == "failed":
        return f"{stage}.failed" if "." not in stage else stage
    if status == "cancelled":
        return "workflow.cancelled"
    if status == "retrying":
        return "retry.started"
    return f"workflow.{status}"


def add_event_by_filename(filename: str, status: str, metadata: Dict[str, Any] | None = None) -> None:
    db = SessionLocal()
    try:
        rp = get_profile_by_filename(db, filename)
        if not rp:
            logger.debug("No profile found for filename %s", filename)
            return
        # build update object
        meta = normalize_event_metadata(status, metadata)
        obj = {
            "status": status,
            "metadata": meta,
        }
        # reuse update_profile_db to append history
        update_profile_db(db, rp.id, obj)
    except Exception:
        logger.exception("Failed to add workflow event")
    finally:
        db.close()
