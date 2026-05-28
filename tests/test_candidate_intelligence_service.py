from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.db_models import Base, ResumeProfile
from services.candidate_intelligence_service import (
    build_candidate_snapshot,
    get_resume_version_detail,
    register_uploaded_resume_version,
    rollback_resume_version,
    sync_candidate_intelligence,
)


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_candidate_profile_and_versions_are_created():
    db = _session()
    try:
        profile = ResumeProfile(id="wf-1", uploaded_filename="123_resume.pdf", parsed_text="resume text", status="uploaded", target_roles='["Data Engineer"]')
        db.add(profile)
        db.commit()
        db.refresh(profile)

        register_uploaded_resume_version(db, profile, "resume text")
        sync_candidate_intelligence(
            db,
            profile,
            "resume text",
            {
                "skills": ["Python", "SQL"],
                "strengths": ["Automation"],
                "missing_skills": ["Leadership"],
                "recommendations": ["Add quantified impact"],
                "ats_score": 84,
            },
            ["Data Engineer"],
            {"event_type": "optimization.completed", "timestamp": "2026-05-28T10:00:00"},
        )
        db.commit()

        candidate_profile, candidate_memory, resume_versions = build_candidate_snapshot(db, profile.uploaded_filename)

        assert candidate_profile["preferred_roles"] == ["Data Engineer"]
        assert candidate_profile["skills"] == ["Python", "SQL"]
        assert len(candidate_memory) >= 2
        assert len(resume_versions) == 2
        assert any(version["version_kind"] == "optimized" for version in resume_versions)
    finally:
        db.close()


def test_resume_version_rollback_marks_target_active():
    db = _session()
    try:
        profile = ResumeProfile(id="wf-2", uploaded_filename="123_resume.pdf", parsed_text="resume text", status="uploaded", target_roles='[]')
        db.add(profile)
        db.commit()
        db.refresh(profile)

        register_uploaded_resume_version(db, profile, "resume text")
        sync_candidate_intelligence(
            db,
            profile,
            "resume text",
            {"ats_score": 90, "recommendations": ["Tighten summary"]},
            [],
            {"event_type": "optimization.completed", "timestamp": "2026-05-28T10:00:00"},
        )
        db.commit()

        _, _, versions = build_candidate_snapshot(db, profile.uploaded_filename)
        uploaded_version = next(version for version in versions if version["version_kind"] == "uploaded")

        result = rollback_resume_version(db, uploaded_version["id"])
        _, _, updated_versions = build_candidate_snapshot(db, profile.uploaded_filename)

        assert result["status"] == "rolled_back"
        assert next(version for version in updated_versions if version["id"] == uploaded_version["id"])["is_active"] is True
    finally:
        db.close()


def test_resume_version_detail_returns_comparison_payload():
    db = _session()
    try:
        profile = ResumeProfile(id="wf-3", uploaded_filename="123_resume.pdf", parsed_text="Python\nSQL", status="uploaded", target_roles='[]')
        db.add(profile)
        db.commit()
        db.refresh(profile)

        register_uploaded_resume_version(db, profile, "Python\nSQL")
        sync_candidate_intelligence(
            db,
            profile,
            "Python\nSQL\nAutomation",
            {
                "ats_score": 84,
                "skills": ["Python", "SQL", "Automation"],
                "recommendations": ["Add quantified impact"],
            },
            [],
            {"event_type": "optimization.completed", "timestamp": "2026-05-28T09:00:00"},
        )
        sync_candidate_intelligence(
            db,
            profile,
            "Python\nSQL\nLeadership",
            {
                "ats_score": 91,
                "skills": ["Python", "SQL", "Leadership"],
                "recommendations": ["Keep quantified impact"],
            },
            [],
            {"event_type": "optimization.completed", "timestamp": "2026-05-28T10:00:00"},
        )
        db.commit()

        _, _, versions = build_candidate_snapshot(db, profile.uploaded_filename)
        optimized_version = next(version for version in versions if version["version_kind"] == "optimized" and version["ats_score"] == 91)
        detail = get_resume_version_detail(db, optimized_version["id"])

        assert detail is not None
        assert detail["comparison"]["added_lines"] == ["Leadership"]
        assert detail["comparison"]["ats_delta"] == 7
        assert detail["previous_version"]["version_label"]
    finally:
        db.close()