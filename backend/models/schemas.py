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
    updated_at: str | None = None
    status: str
    target_roles: list[str] = Field(default_factory=list)
    profile: dict | None = None
    ats_score: float | None = None
    progress_percentage: int | float = 0
    current_stage: str = "queued"
    current_stage_label: str = "Workflow queued"
    current_stage_state: str = "queued"
    workflow_duration_seconds: float | None = None
    last_activity: str | None = None
    queued_actions: list[str] = Field(default_factory=list)
    execution_metadata: dict = Field(default_factory=dict)
    execution_summary: str = ""
    timeline: list[dict] = Field(default_factory=list)
    available_actions: list[dict] = Field(default_factory=list)
    stage_actions: list[dict] = Field(default_factory=list)
    retry_count: int = 0
    retry_history: list[dict] = Field(default_factory=list)
    failure_reason: str | None = None
    candidate_profile: dict = Field(default_factory=dict)
    candidate_memory: list[dict] = Field(default_factory=list)
    resume_versions: list[dict] = Field(default_factory=list)
    failure_diagnostics: dict = Field(default_factory=dict)


class WorkflowActivityItem(BaseModel):
    workflow_id: str
    filename: str
    timestamp: str | None = None
    status: str
    stage: str
    label: str
    state: str
    source: str = "workflow-engine"
    event_type: str = "workflow.event"
    severity: str = "info"


class WorkflowOverview(BaseModel):
    active: int = 0
    completed: int = 0
    failed: int = 0
    queued: int = 0
    total: int = 0


class QueueSnapshot(BaseModel):
    size: int = 0
    pending: list[dict] = Field(default_factory=list)


class TransportCapabilities(BaseModel):
    mode: str = "sse-primary"
    supported: list[str] = Field(default_factory=list)
    contract: str = "workflow-status-payload-v1"
    event_contract: str = "workflow-event-envelope-v1"
    event_version: int = 1
    metadata_contract: str = "workflow-metadata-v1"
    metadata_version: int = 1
    filters: list[str] = Field(default_factory=list)
    recovery: list[str] = Field(default_factory=list)


class WorkflowContractManifest(BaseModel):
    status_payload: str = "workflow-status-payload-v1"
    event_envelope: str = "workflow-event-envelope-v1"
    event_version: int = 1
    metadata: str = "workflow-metadata-v1"
    metadata_version: int = 1


class IntegrationSeamItem(BaseModel):
    status: str = "planned"
    integration_type: str = "adapter"
    contract: str = "workflow-event-envelope-v1"
    entrypoint: str = "workflow events"


class EventAggregationBucket(BaseModel):
    key: str
    count: int


class WorkflowEventQueryResponse(BaseModel):
    results: list[dict] = Field(default_factory=list)
    total: int = 0
    filters: dict = Field(default_factory=dict)
    page: int = 1
    page_size: int = 40
    pages: int = 1
    aggregations: dict[str, list[EventAggregationBucket]] = Field(default_factory=dict)


class ResumeVersionReference(BaseModel):
    id: str
    version_label: str
    ats_score: float | None = None


class ResumeVersionComparison(BaseModel):
    current_text: str = ""
    previous_text: str = ""
    added_lines: list[str] = Field(default_factory=list)
    removed_lines: list[str] = Field(default_factory=list)
    ats_delta: float | None = None
    current_analysis: dict = Field(default_factory=dict)
    previous_analysis: dict = Field(default_factory=dict)


class ResumeVersionDetailResponse(BaseModel):
    id: str
    version_kind: str = ""
    version_label: str = ""
    source_filename: str | None = None
    ats_score: float | None = None
    change_summary: str | None = None
    diff_summary: str | None = None
    is_active: bool = False
    created_at: str | None = None
    previous_version: ResumeVersionReference | None = None
    comparison: ResumeVersionComparison = Field(default_factory=ResumeVersionComparison)


class ResumeVersionRollbackResponse(BaseModel):
    version_id: str
    candidate_key: str
    version_label: str
    status: str


class WorkflowStatusResponse(BaseModel):
    profiles: list[ProfileItem] = Field(default_factory=list)
    activity_feed: list[WorkflowActivityItem] = Field(default_factory=list)
    overview: WorkflowOverview = Field(default_factory=WorkflowOverview)
    queue: QueueSnapshot = Field(default_factory=QueueSnapshot)
    automation_placeholders: dict = Field(default_factory=dict)
    transport: TransportCapabilities = Field(default_factory=TransportCapabilities)
    contracts: WorkflowContractManifest = Field(default_factory=WorkflowContractManifest)
    analytics: dict = Field(default_factory=dict)
    observability: dict = Field(default_factory=dict)
    event_query: WorkflowEventQueryResponse = Field(default_factory=WorkflowEventQueryResponse)
    integration_seams: dict[str, IntegrationSeamItem] = Field(default_factory=dict)
    active_filters: dict = Field(default_factory=dict)


class WorkflowActionRequest(BaseModel):
    action: str = Field(..., min_length=3, max_length=20)
    stage: str | None = None


class WorkflowActionResponse(BaseModel):
    workflow_id: str
    action: str
    status: str
    message: str
    stage: str | None = None
