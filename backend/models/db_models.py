from sqlalchemy import Column, String, Text, DateTime, Float
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
