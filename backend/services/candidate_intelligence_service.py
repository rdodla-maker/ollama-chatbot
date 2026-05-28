"""Candidate intelligence, memory, and resume versioning helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from models.db_models import CandidateMemory, CandidateProfile, ResumeProfile, ResumeVersion


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True)


def derive_candidate_key(uploaded_filename: str | None) -> str:
    filename = Path(uploaded_filename or "candidate").name
    stem = Path(filename).stem
    if "_" in stem:
        stem = stem.split("_", 1)[1]
    return stem.lower().replace(" ", "-") or "candidate"


def _display_name(candidate_key: str) -> str:
    return candidate_key.replace("-", " ").replace("_", " ").title()


def _merge_unique(existing: list[Any], incoming: list[Any]) -> list[Any]:
    out: list[Any] = []
    seen: set[str] = set()
    for item in [*(existing or []), *(incoming or [])]:
        if item in (None, ""):
            continue
        marker = json.dumps(item, sort_keys=True, default=str)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def _append_memory(db: Session, candidate_key: str, memory_type: str, content: dict[str, Any]) -> None:
    payload = _dumps(content)
    last_entry = (
        db.query(CandidateMemory)
        .filter(CandidateMemory.candidate_key == candidate_key, CandidateMemory.memory_type == memory_type)
        .order_by(CandidateMemory.created_at.desc())
        .first()
    )
    if last_entry and last_entry.content == payload:
        return
    db.add(CandidateMemory(candidate_key=candidate_key, memory_type=memory_type, content=payload))


def _ensure_candidate_profile(db: Session, candidate_key: str) -> CandidateProfile:
    candidate = db.query(CandidateProfile).filter(CandidateProfile.candidate_key == candidate_key).first()
    if candidate:
        return candidate
    candidate = CandidateProfile(
        candidate_key=candidate_key,
        display_name=_display_name(candidate_key),
        preferred_roles=_dumps([]),
        skills=_dumps([]),
        strengths=_dumps([]),
        weaknesses=_dumps([]),
        ats_history=_dumps([]),
        optimization_history=_dumps([]),
    )
    db.add(candidate)
    db.flush()
    return candidate


def register_uploaded_resume_version(db: Session, resume_profile: ResumeProfile, parsed_text: str | None) -> None:
    candidate_key = derive_candidate_key(resume_profile.uploaded_filename)
    _ensure_candidate_profile(db, candidate_key)
    existing = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_profile_id == resume_profile.id, ResumeVersion.version_kind == "uploaded")
        .first()
    )
    if existing:
        return
    version = ResumeVersion(
        candidate_key=candidate_key,
        resume_profile_id=resume_profile.id,
        version_kind="uploaded",
        version_label="Uploaded resume",
        source_filename=resume_profile.uploaded_filename,
        content_snapshot=(parsed_text or "")[:12000],
        change_summary="Original uploaded resume snapshot.",
        diff_summary="Initial baseline version.",
        is_active=True,
    )
    db.query(ResumeVersion).filter(ResumeVersion.candidate_key == candidate_key).update({ResumeVersion.is_active: False})
    db.add(version)
    _append_memory(
        db,
        candidate_key,
        "resume_upload",
        {"uploaded_filename": resume_profile.uploaded_filename, "resume_profile_id": resume_profile.id},
    )


def sync_candidate_intelligence(
    db: Session,
    resume_profile: ResumeProfile,
    parsed_text: str | None,
    parsed_analysis: dict[str, Any] | None,
    target_roles: list[str],
    metadata: dict[str, Any] | None = None,
) -> None:
    candidate_key = derive_candidate_key(resume_profile.uploaded_filename)
    candidate = _ensure_candidate_profile(db, candidate_key)
    metadata = metadata or {}
    parsed_analysis = parsed_analysis or {}

    candidate.preferred_roles = _dumps(_merge_unique(_loads(candidate.preferred_roles, []), target_roles or []))
    candidate.skills = _dumps(_merge_unique(_loads(candidate.skills, []), parsed_analysis.get("skills") or []))
    candidate.strengths = _dumps(_merge_unique(_loads(candidate.strengths, []), parsed_analysis.get("strengths") or []))
    candidate.weaknesses = _dumps(_merge_unique(_loads(candidate.weaknesses, []), parsed_analysis.get("missing_skills") or []))

    ats_history = _loads(candidate.ats_history, [])
    ats_score = parsed_analysis.get("ats_score")
    if ats_score is not None:
        ats_history.append(
            {
                "ats_score": ats_score,
                "timestamp": metadata.get("timestamp"),
                "resume_profile_id": resume_profile.id,
            }
        )
    candidate.ats_history = _dumps(ats_history[-12:])

    optimization_history = _loads(candidate.optimization_history, [])
    if metadata.get("event_type") in {"optimization.completed", "analysis.completed"} or parsed_analysis:
        optimization_history.append(
            {
                "resume_profile_id": resume_profile.id,
                "ats_score": ats_score,
                "roles": target_roles or [],
                "event_type": metadata.get("event_type") or "optimization.completed",
                "timestamp": metadata.get("timestamp"),
            }
        )
    candidate.optimization_history = _dumps(optimization_history[-12:])

    db.add(candidate)

    if target_roles:
        _append_memory(db, candidate_key, "preferred_roles", {"roles": target_roles})
    if parsed_analysis.get("missing_skills"):
        _append_memory(db, candidate_key, "ats_gaps", {"missing_skills": parsed_analysis.get("missing_skills")})
    if parsed_analysis.get("recommendations"):
        _append_memory(db, candidate_key, "optimization_history", {"recommendations": parsed_analysis.get("recommendations")})

    if parsed_analysis:
        previous_active = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.candidate_key == candidate_key, ResumeVersion.is_active.is_(True))
            .order_by(ResumeVersion.created_at.desc())
            .first()
        )
        previous_score = previous_active.ats_score if previous_active else None
        next_snapshot = _dumps(
            {
                "parsed_text_snippet": (parsed_text or "")[:4000],
                "analysis": parsed_analysis,
            }
        )
        has_changed = not previous_active or previous_active.content_snapshot != next_snapshot or previous_active.ats_score != ats_score
        if has_changed:
            db.query(ResumeVersion).filter(ResumeVersion.candidate_key == candidate_key).update({ResumeVersion.is_active: False})
            db.add(
                ResumeVersion(
                    candidate_key=candidate_key,
                    resume_profile_id=resume_profile.id,
                    version_kind="optimized",
                    version_label="AI optimized intelligence snapshot",
                    source_filename=resume_profile.uploaded_filename,
                    content_snapshot=next_snapshot,
                    ats_score=ats_score,
                    change_summary="ATS optimization snapshot created from workflow analysis.",
                    diff_summary=(
                        f"ATS delta {round((ats_score or 0) - (previous_score or 0), 2)}"
                        if ats_score is not None and previous_score is not None
                        else "First optimization snapshot."
                    ),
                    previous_version_id=previous_active.id if previous_active else None,
                    is_active=True,
                )
            )


def build_candidate_snapshot(db: Session, uploaded_filename: str | None) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_key = derive_candidate_key(uploaded_filename)
    candidate = db.query(CandidateProfile).filter(CandidateProfile.candidate_key == candidate_key).first()
    if not candidate:
        return {}, [], []

    memory_rows = (
        db.query(CandidateMemory)
        .filter(CandidateMemory.candidate_key == candidate_key)
        .order_by(CandidateMemory.created_at.desc())
        .limit(8)
        .all()
    )
    version_rows = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.candidate_key == candidate_key)
        .order_by(ResumeVersion.created_at.desc())
        .limit(8)
        .all()
    )

    profile = {
        "candidate_key": candidate.candidate_key,
        "display_name": candidate.display_name,
        "preferred_roles": _loads(candidate.preferred_roles, []),
        "skills": _loads(candidate.skills, []),
        "strengths": _loads(candidate.strengths, []),
        "weaknesses": _loads(candidate.weaknesses, []),
        "ats_history": _loads(candidate.ats_history, []),
        "optimization_history": _loads(candidate.optimization_history, []),
    }
    memory = [
        {
            "id": row.id,
            "memory_type": row.memory_type,
            "content": _loads(row.content, {}),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in memory_rows
    ]
    versions = [
        {
            "id": row.id,
            "version_kind": row.version_kind,
            "version_label": row.version_label,
            "source_filename": row.source_filename,
            "ats_score": row.ats_score,
            "change_summary": row.change_summary,
            "diff_summary": row.diff_summary,
            "previous_version_id": row.previous_version_id,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in version_rows
    ]
    return profile, memory, versions


def get_resume_version_detail(db: Session, version_id: str) -> dict[str, Any] | None:
    version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
    if not version:
        return None
    previous = db.query(ResumeVersion).filter(ResumeVersion.id == version.previous_version_id).first() if version.previous_version_id else None

    current_payload = _loads(version.content_snapshot, version.content_snapshot or "")
    previous_payload = _loads(previous.content_snapshot, previous.content_snapshot or "") if previous else ""

    current_text = current_payload.get("parsed_text_snippet") if isinstance(current_payload, dict) else str(current_payload or "")
    previous_text = previous_payload.get("parsed_text_snippet") if isinstance(previous_payload, dict) else str(previous_payload or "")
    current_analysis = current_payload.get("analysis") if isinstance(current_payload, dict) else {}
    previous_analysis = previous_payload.get("analysis") if isinstance(previous_payload, dict) else {}

    current_lines = [line.strip() for line in current_text.splitlines() if line.strip()]
    previous_lines = [line.strip() for line in previous_text.splitlines() if line.strip()]
    added = [line for line in current_lines if line not in previous_lines][:12]
    removed = [line for line in previous_lines if line not in current_lines][:12]

    return {
        "id": version.id,
        "version_kind": version.version_kind,
        "version_label": version.version_label,
        "source_filename": version.source_filename,
        "ats_score": version.ats_score,
        "change_summary": version.change_summary,
        "diff_summary": version.diff_summary,
        "is_active": version.is_active,
        "created_at": version.created_at.isoformat() if version.created_at else None,
        "previous_version": {
            "id": previous.id,
            "version_label": previous.version_label,
            "ats_score": previous.ats_score,
        }
        if previous
        else None,
        "comparison": {
            "current_text": current_text,
            "previous_text": previous_text,
            "added_lines": added,
            "removed_lines": removed,
            "ats_delta": None if version.ats_score is None or not previous or previous.ats_score is None else round(version.ats_score - previous.ats_score, 2),
            "current_analysis": current_analysis,
            "previous_analysis": previous_analysis,
        },
    }


def rollback_resume_version(db: Session, version_id: str) -> dict[str, Any] | None:
    version = db.query(ResumeVersion).filter(ResumeVersion.id == version_id).first()
    if not version:
        return None
    db.query(ResumeVersion).filter(ResumeVersion.candidate_key == version.candidate_key).update({ResumeVersion.is_active: False})
    version.is_active = True
    db.add(version)
    _append_memory(
        db,
        version.candidate_key,
        "rollback",
        {"version_id": version.id, "version_label": version.version_label},
    )
    db.commit()
    db.refresh(version)
    return {
        "version_id": version.id,
        "candidate_key": version.candidate_key,
        "version_label": version.version_label,
        "status": "rolled_back",
    }