"""Profile store that prefers SQLite via repository, falls back to JSON file."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

from core.config import settings

STORE_PATH = Path(settings.application_memory_path).parent / "resume_profiles.json"

_use_db = False
try:
    from db import init_db, SessionLocal
    from services.repository import (
        create_profile_db,
        update_profile_db,
        list_profiles_db,
        get_profile_by_filename,
    )

    init_db()
    _use_db = True
except Exception:
    _use_db = False


def _load() -> list[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(records: list[dict]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def create_profile(uploaded_filename: str, parsed_text: str, target_roles: list[str]) -> dict:
    if _use_db:
        db = SessionLocal()
        try:
            rp = create_profile_db(db, uploaded_filename, parsed_text, target_roles)
            return {
                "id": rp.id,
                "uploaded_filename": rp.uploaded_filename,
                "created_at": rp.created_at.isoformat() if rp.created_at else None,
                "status": rp.status,
            }
        finally:
            db.close()

    profile_id = str(uuid.uuid4())
    item = {
        "id": profile_id,
        "uploaded_filename": uploaded_filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "uploaded",
        "target_roles": target_roles,
        "parsed_text_snippet": parsed_text[:2000],
        "profile": None,
    }
    records = _load()
    records.append(item)
    _save(records[-500:])
    return item


def update_profile(profile_id: str, profile_obj: dict) -> dict | None:
    if _use_db:
        db = SessionLocal()
        try:
            rp = update_profile_db(db, profile_id, profile_obj)
            if not rp:
                return None
            return {
                "id": rp.id,
                "uploaded_filename": rp.uploaded_filename,
                "created_at": rp.created_at.isoformat() if rp.created_at else None,
                "status": rp.status,
            }
        finally:
            db.close()

    records = _load()
    for r in records:
        if r.get("id") == profile_id:
            r["profile"] = profile_obj
            r["status"] = "analyzed"
            _save(records[-500:])
            return r
    return None


def list_profiles() -> list[dict]:
    if _use_db:
        db = SessionLocal()
        try:
            return list_profiles_db(db)
        finally:
            db.close()
    return list(reversed(_load()))


