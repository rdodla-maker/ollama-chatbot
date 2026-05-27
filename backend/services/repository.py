from typing import List, Optional
from sqlalchemy.orm import Session
from models.db_models import ResumeProfile
from datetime import datetime
import json


def create_profile_db(db: Session, uploaded_filename: str, parsed_text: str, target_roles: List[str]) -> ResumeProfile:
    rp = ResumeProfile(
        uploaded_filename=uploaded_filename,
        parsed_text=(parsed_text or "")[:20000],
        target_roles=json.dumps(target_roles or []),
        status="uploaded",
    )
    db.add(rp)
    db.commit()
    db.refresh(rp)
    return rp


def update_profile_db(db: Session, profile_id: str, profile_obj: dict) -> Optional[ResumeProfile]:
    rp = db.query(ResumeProfile).filter(ResumeProfile.id == profile_id).first()
    if not rp:
        return None
    # merge fields
    rp.analysis_raw = profile_obj.get("analysis_raw") or rp.analysis_raw
    parsed = profile_obj.get("parsed")
    try:
        rp.analysis_json = json.dumps(parsed) if parsed is not None else rp.analysis_json
    except Exception:
        rp.analysis_json = None
    rp.target_roles = json.dumps(profile_obj.get("target_roles") or json.loads(rp.target_roles or "[]"))
    rp.status = profile_obj.get("status") or "analyzed"
    rp.ats_score = profile_obj.get("ats_score") or rp.ats_score
    # append to workflow history
    history = rp.workflow_history or "[]"
    try:
        hist = json.loads(history)
    except Exception:
        hist = []
    hist.append({"when": datetime.utcnow().isoformat(), "status": rp.status})
    rp.workflow_history = json.dumps(hist)
    db.add(rp)
    db.commit()
    db.refresh(rp)
    return rp


def list_profiles_db(db: Session) -> List[dict]:
    rows = db.query(ResumeProfile).order_by(ResumeProfile.created_at.desc()).all()
    out = []
    for r in rows:
        try:
            target_roles = json.loads(r.target_roles) if r.target_roles else []
        except Exception:
            target_roles = []
        try:
            parsed = json.loads(r.analysis_json) if r.analysis_json else None
        except Exception:
            parsed = None
        out.append(
            {
                "id": r.id,
                "uploaded_filename": r.uploaded_filename,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "status": r.status,
                "target_roles": target_roles,
                "profile": parsed,
                "ats_score": r.ats_score,
            }
        )
    return out


def get_profile_by_filename(db: Session, filename: str) -> Optional[ResumeProfile]:
    return db.query(ResumeProfile).filter(ResumeProfile.uploaded_filename == filename).first()
