"""API request and response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class SourceChunk(BaseModel):
    text: str
    metadata: dict = Field(default_factory=dict)
    distance: float | None = None


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceChunk] = Field(default_factory=list)


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class AgentResponse(BaseModel):
    response: str
    reasoning: list[str]
    plan: str


class GenerateApplicationRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=20, max_length=12000)
    skills: str = Field(..., min_length=2, max_length=4000)
    resume_text: str = Field(..., min_length=20, max_length=12000)
    tone: str = Field(..., min_length=2, max_length=50)


class GenerateApplicationResponse(BaseModel):
    generated_email: str
    generated_cover_letter: str
    resume_suggestions: str


class ApplicationTrackerItem(BaseModel):
    company: str
    role: str
    application_date: str
    status: str
    generated_email: str = ""
    generated_cover_letter: str = ""


class ApplicationTrackerResponse(BaseModel):
    applications: list[ApplicationTrackerItem] = Field(default_factory=list)


class UploadResponse(BaseModel):
    message: str
    chunks: int
    document_id: str = ""


class CodebaseIndexResponse(BaseModel):
    message: str
    files: int = 0
    chunks: int = 0


class PendingChangeSummary(BaseModel):
    id: str
    file_path: str
    status: str
    created_at: str
    preview: str = ""


class PendingChangeDetail(BaseModel):
    id: str
    file_path: str
    status: str
    created_at: str
    new_content: str
    original_preview: str = ""


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class ResumeUploadResponse(BaseModel):
    upload_id: str
    filename: str
    parsed_snippet: str | None = None


class AnalyzeResumeRequest(BaseModel):
    upload_id: str | None = None
    resume_text: str | None = None
    target_roles: list[str] = Field(default_factory=list)


class AnalyzeResumeResponse(BaseModel):
    upload_id: str | None = None
    profile_id: str | None = None
    analysis_raw: str
    parsed: dict | None = None
    ats_score: float | None = None
    role_compatibility: dict | None = None


class ProfileItem(BaseModel):
    id: str
    uploaded_filename: str
    created_at: str
    status: str
    target_roles: list[str] = Field(default_factory=list)
    profile: dict | None = None
    ats_score: float | None = None


class WorkflowStatusResponse(BaseModel):
    profiles: list[ProfileItem] = Field(default_factory=list)
