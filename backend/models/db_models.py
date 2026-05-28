from sqlalchemy import Boolean, Column, String, Text, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from uuid import uuid4
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    uploaded_filename = Column(String(512), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String(64), nullable=False, default="uploaded")
    target_roles = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    analysis_raw = Column(Text, nullable=True)
    analysis_json = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    workflow_history = Column(Text, nullable=True)


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    candidate_key = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    preferred_roles = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    ats_history = Column(Text, nullable=True)
    optimization_history = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CandidateMemory(Base):
    __tablename__ = "candidate_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    candidate_key = Column(String(255), nullable=False, index=True)
    memory_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    candidate_key = Column(String(255), nullable=False, index=True)
    resume_profile_id = Column(String(36), nullable=True, index=True)
    version_kind = Column(String(64), nullable=False)
    version_label = Column(String(255), nullable=False)
    source_filename = Column(String(512), nullable=True)
    content_snapshot = Column(Text, nullable=True)
    ats_score = Column(Float, nullable=True)
    change_summary = Column(Text, nullable=True)
    diff_summary = Column(Text, nullable=True)
    previous_version_id = Column(String(36), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
