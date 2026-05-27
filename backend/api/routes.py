"""API routes — async handlers, streaming, and codebase indexing."""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool

from agent import ask_agent
from agent.runner import stream_agent_events
from core.config import settings
from core.exceptions import OllamaConnectionError
from core.logging_config import get_logger
from models.schemas import (
    AgentRequest,
    AgentResponse,
    ApplicationTrackerResponse,
    ChatRequest,
    ChatResponse,
    CodebaseIndexResponse,
    GenerateApplicationRequest,
    GenerateApplicationResponse,
    SourceChunk,
    UploadResponse,
    ResumeUploadResponse,
    AnalyzeResumeRequest,
    AnalyzeResumeResponse,
    WorkflowStatusResponse,
    WorkflowActionRequest,
    WorkflowActionResponse,
)
from rag.codebase_index import index_codebase
from rag.vector_store import ingest_pdf, search_chunks_with_metadata
from services.ollama_service import generate_completion, stream_completion
from services.application_service import generate_application_materials
from services.application_tracking_service import (
    append_application_record,
    list_application_records,
)
from services.google_sheets_service import append_application_to_sheet
from services.resume_parsing_service import extract_text_from_resume
from services.profile_store import create_profile, update_profile, list_profiles
from services.workflow_status_service import build_workflow_status_payload
from services.workflow_orchestration_service import apply_workflow_action
from services.workflow_event_bus import build_snapshot_event, subscribe, unsubscribe
import uuid
from pathlib import Path
import json

logger = get_logger("api")

router = APIRouter()


def _sse_data(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _safe_filename(name: str) -> str:
    clean = Path(name).name
    if not clean or clean in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    return clean


@router.get("/")
async def root():
    return {
        "message": "RAG AI Backend Running",
        "version": "3.0.0",
        "agent_mode": "langgraph" if settings.use_langgraph_agent else "legacy",
        "model": settings.ollama_model,
        "ollama_url": settings.ollama_base_url,
    }


@router.get("/memory")
async def get_memory():
    """Return agent long-term memory entries for the UI."""
    from memory.store import memory_store

    return {
        "entries": list(reversed(memory_store.entries)),
        "count": len(memory_store.entries),
    }


@router.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    safe_name = _safe_filename(file.filename)
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_name

    try:
        content = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.max_upload_mb} MB.",
            )

        file_path.write_bytes(content)

        chunk_count, document_id = await asyncio.to_thread(
            ingest_pdf, str(file_path), safe_name
        )

        return UploadResponse(
            message="PDF uploaded successfully",
            chunks=chunk_count,
            document_id=document_id,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Failed to process PDF upload.") from exc



@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")
    if not (file.filename.lower().endswith('.pdf') or file.filename.lower().endswith('.docx') or file.filename.lower().endswith('.doc')):
        raise HTTPException(status_code=400, detail="Only PDF/DOCX files are allowed.")

    safe_name = _safe_filename(file.filename)
    upload_dir = Path(settings.upload_dir) / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)
    uid = str(uuid.uuid4())
    file_path = upload_dir / f"{uid}_{safe_name}"

    try:
        content = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.max_upload_mb} MB.",
            )

        # Basic MIME/content type validation
        ctype = getattr(file, "content_type", "") or ""
        if ctype and not (
            ctype.startswith("application/pdf") or "word" in ctype or ctype == "application/octet-stream"
        ):
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {ctype}")

        file_path.write_bytes(content)

        # parse resume text (best-effort)
        try:
            parsed_text, ftype = await asyncio.to_thread(extract_text_from_resume, str(file_path))
        except Exception as exc:
            logger.exception("Resume parse failed on upload")
            parsed_text = ""

        # create profile placeholder (DB-backed if configured)
        profile = await asyncio.to_thread(create_profile, file_path.name, parsed_text, [])

        # enqueue background analysis task (placeholder)
        try:
            from services.task_queue import enqueue_task

            enqueue_task({"type": "analyze_resume", "upload_id": file_path.name, "workflow_id": profile.get("id")})
        except Exception:
            logger.debug("Task queue not available; skipping enqueue")

        return ResumeUploadResponse(upload_id=file_path.name, filename=file_path.name, parsed_snippet=(parsed_text or "")[:1000])
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Resume upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload resume.") from exc



@router.post("/analyze-resume", response_model=AnalyzeResumeResponse)
async def analyze_resume(body: AnalyzeResumeRequest):
    # Validate roles
    roles = body.target_roles or []
    if len(roles) > 5:
        raise HTTPException(status_code=400, detail="A maximum of 5 target roles is allowed.")

    # obtain resume text
    resume_text = None
    upload_id = body.upload_id
    if upload_id:
        candidate = Path(settings.upload_dir) / "resumes" / upload_id
        if not candidate.exists():
            raise HTTPException(status_code=404, detail="Upload not found")
        try:
            resume_text, _ = await asyncio.to_thread(extract_text_from_resume, str(candidate))
        except Exception:
            resume_text = candidate.read_text(encoding="utf-8", errors="ignore")[:10000]
    elif body.resume_text:
        resume_text = body.resume_text
    else:
        raise HTTPException(status_code=400, detail="No resume text or upload_id provided.")

    # Use shared analysis service to analyze and persist results
    try:
        from services.analysis_service import analyze_and_persist

        analysis = await analyze_and_persist(upload_id, resume_text, roles)
    except Exception as exc:
        logger.exception("Analysis service failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    parsed = analysis.get("parsed")
    ats_score = None
    role_compat = None
    if isinstance(parsed, dict):
        ats_score = parsed.get("ats_score")
        role_compat = parsed.get("role_compatibility")

    # find profile id if available
    profile_id = None
    if upload_id:
        try:
            records = await asyncio.to_thread(list_profiles)
            for r in records:
                if r.get("uploaded_filename") == upload_id:
                    profile_id = r.get("id")
                    break
        except Exception:
            logger.debug("Could not locate profile id after analysis")

    return AnalyzeResumeResponse(upload_id=upload_id, profile_id=profile_id, analysis_raw=analysis.get("analysis_raw"), parsed=parsed, ats_score=ats_score, role_compatibility=role_compat)



@router.get("/workflow-status", response_model=WorkflowStatusResponse)
async def workflow_status():
    records = await asyncio.to_thread(list_profiles)
    try:
        from services.task_queue import get_queue_snapshot

        queue_snapshot = get_queue_snapshot()
    except Exception:
        queue_snapshot = {"size": 0, "pending": []}
    payload = build_workflow_status_payload(records, queue_snapshot)
    return WorkflowStatusResponse(**payload)


@router.get("/workflow-status/stream")
async def workflow_status_stream(request: Request):
    subscriber_id, event_queue = subscribe()

    async def event_stream():
        try:
            yield _sse_data(build_snapshot_event())
            while True:
                if await request.is_disconnected():
                    break
                try:
                    envelope = await asyncio.wait_for(asyncio.to_thread(event_queue.get, True, 10), timeout=12)
                    yield _sse_data(envelope)
                except asyncio.TimeoutError:
                    yield _sse_data({"type": "heartbeat", "timestamp": asyncio.get_running_loop().time()})
        finally:
            unsubscribe(subscriber_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/workflow-status/{workflow_id}/action", response_model=WorkflowActionResponse)
async def workflow_action(workflow_id: str, body: WorkflowActionRequest):
    try:
        result = await asyncio.to_thread(apply_workflow_action, workflow_id, body.action, body.stage)
        return WorkflowActionResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/index-codebase", response_model=CodebaseIndexResponse)
async def index_codebase_route():
    """Index backend/ and frontend/src/ for semantic code search."""
    try:
        stats = await asyncio.to_thread(index_codebase)
        return CodebaseIndexResponse(
            message=stats.get("message", "Indexing complete."),
            files=stats.get("files", 0),
            chunks=stats.get("chunks", 0),
        )
    except Exception as exc:
        logger.exception("Codebase indexing failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to index codebase.",
        ) from exc


def _build_rag_prompt(user_message: str, context: str) -> str:
    return f"""Use the context below to answer the question.

Context:
{context}

Question:
{user_message}

Answer clearly and accurately."""


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    user_message = body.message

    try:
        matches = await asyncio.to_thread(
            search_chunks_with_metadata, user_message
        )

        if not matches:
            return ChatResponse(
                response=(
                    "No PDF documents are indexed yet, or no relevant "
                    "content was found. Please upload a PDF first."
                ),
                sources=[],
            )

        sources: list[SourceChunk] = []
        context_parts = []
        for match in matches:
            context_parts.append(match["text"])
            sources.append(
                SourceChunk(
                    text=match["text"],
                    metadata=match.get("metadata", {}),
                    distance=match.get("distance"),
                )
            )

        prompt = _build_rag_prompt(user_message, "\n\n".join(context_parts))
        ai_response = await generate_completion(prompt)

        return ChatResponse(response=ai_response, sources=sources)

    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chat endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question.",
        ) from exc


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    """Stream RAG chat response via Server-Sent Events."""
    user_message = body.message

    try:
        matches = await asyncio.to_thread(
            search_chunks_with_metadata, user_message
        )

        if not matches:
            async def empty_stream():
                msg = (
                    "No PDF documents are indexed yet. "
                    "Please upload a PDF first."
                )
                yield f"data: {json.dumps({'token': msg, 'done': True})}\n\n"

            return StreamingResponse(empty_stream(), media_type="text/event-stream")

        context = "\n\n".join(m["text"] for m in matches)
        prompt = _build_rag_prompt(user_message, context)

        async def event_stream():
            try:
                async for token in stream_completion(prompt):
                    yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
            except OllamaConnectionError as exc:
                yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/agent", response_model=AgentResponse)
async def agent_chat(body: AgentRequest):
    try:
        agent_result = await asyncio.to_thread(ask_agent, body.message)
        return AgentResponse(
            reasoning=agent_result.get("reasoning", []),
            plan=agent_result.get("plan", ""),
            response=agent_result.get("response", ""),
        )
    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Agent endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while running the agent.",
        ) from exc


@router.post("/agent/stream")
async def agent_stream(body: AgentRequest):
    """Stream agent plan, reasoning steps, and response tokens via SSE."""

    async def event_generator():
        async for event in iterate_in_threadpool(
            stream_agent_events(body.message)
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/generate-application", response_model=GenerateApplicationResponse)
async def generate_application(body: GenerateApplicationRequest):
    try:
        result = await generate_application_materials(body)
        record = await asyncio.to_thread(
            append_application_record,
            body.company,
            body.role,
            result["generated_email"],
            result["generated_cover_letter"],
        )
        await asyncio.to_thread(append_application_to_sheet, record)
        return GenerateApplicationResponse(**result)
    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Generate application endpoint failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate application materials.",
        ) from exc


@router.get("/application-tracker", response_model=ApplicationTrackerResponse)
async def application_tracker():
    records = await asyncio.to_thread(list_application_records)
    return ApplicationTrackerResponse(applications=records)
