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
