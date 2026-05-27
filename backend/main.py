"""
FastAPI application entry point.

Run from the backend directory:
  uvicorn main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

from api.pending_routes import router as pending_router
from api.routes import router
from core.config import settings
from core.logging_config import setup_logging, get_logger
from core.tracing import setup_langsmith_tracing
from models.schemas import ErrorResponse

# Initialize logging before other imports load heavy models
setup_logging()
setup_langsmith_tracing()
logger = get_logger("api")

# Ensure data directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Agentic AI Backend",
    description="Ollama + RAG + Autonomous Agent API",
    version="3.0.0",
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:  # ensure we log unexpected exceptions
            status = 500
            raise
        finally:
            duration = (time.time() - start) * 1000
            logger.info(
                "%s %s %s %.2fms",
                request.method,
                request.url.path,
                status,
                duration,
            )
        return response


app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(pending_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail if isinstance(exc.detail, str) else "Request failed",
            detail=str(exc.detail) if not isinstance(exc.detail, str) else None,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail="An unexpected error occurred.",
        ).model_dump(),
    )


@app.on_event("startup")
async def on_startup():
    logger.info("Backend started — Ollama model: %s", settings.ollama_model)
    logger.info("Allowed filesystem root: %s", settings.allowed_fs_root)
    # Initialize SQLite database and background worker scaffolding
    try:
        from db import init_db
        from services.task_queue import start_worker_in_background

        init_db()
        start_worker_in_background()
        logger.info("Database initialized and background worker started")
    except Exception:
        logger.exception("Failed to initialize DB or background worker")
