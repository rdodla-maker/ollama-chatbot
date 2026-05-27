"""Local tracker persistence for the MVP application flow."""

import json
from datetime import datetime, timezone
from pathlib import Path

from core.config import settings


TRACKER_PATH = Path(settings.application_memory_path)


def _load() -> list[dict]:
    if not TRACKER_PATH.exists():
        return []
    try:
        return json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(records: list[dict]) -> None:
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def append_application_record(
    company: str,
    role: str,
    generated_email: str,
    generated_cover_letter: str,
    status: str = "pending",
) -> dict:
    records = _load()
    record = {
        "company": company,
        "role": role,
        "application_date": datetime.now(timezone.utc).date().isoformat(),
        "status": status,
        "generated_email": generated_email,
        "generated_cover_letter": generated_cover_letter,
    }
    records.append(record)
    _save(records[-300:])
    return record


def list_application_records() -> list[dict]:
    records = _load()
    return list(reversed(records))