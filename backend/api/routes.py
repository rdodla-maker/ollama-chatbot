"""API routes — async handlers, streaming, and codebase indexing."""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
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
    ChatRequest,
    ChatResponse,
    CodebaseIndexResponse,
    SourceChunk,
    UploadResponse,
)
from rag.codebase_index import index_codebase
from rag.vector_store import ingest_pdf, search_chunks_with_metadata
from services.ollama_service import generate_completion, stream_completion

logger = get_logger("api")

router = APIRouter()


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
