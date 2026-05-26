"""Codebase semantic index in ChromaDB."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

import chromadb

from core.config import PROJECT_ROOT, settings
from core.logging_config import get_logger
from core.security import is_ignored_dir, is_likely_binary
from rag.chunking import chunk_text
from rag.embeddings import get_embedding_model

logger = get_logger("rag")

CODEBASE_COLLECTION = "codebase"
INDEX_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".css", ".html"}

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_path)
    return _client


def _get_codebase_collection():
    return _get_client().get_or_create_collection(name=CODEBASE_COLLECTION)


def _iter_code_files() -> list[Path]:
    files: list[Path] = []
    for rel in settings.codebase_path_list:
        base = (PROJECT_ROOT / rel).resolve()
        if not base.exists():
            logger.warning("Codebase path not found: %s", base)
            continue
        if base.is_file():
            if base.suffix.lower() in INDEX_EXTENSIONS:
                files.append(base)
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in INDEX_EXTENSIONS:
                continue
            if any(p in IGNORED_PARTS for p in path.parts):
                continue
            if is_likely_binary(path):
                continue
            files.append(path)
    return files


IGNORED_PARTS = {
    "venv", "node_modules", ".git", "dist", "build",
    "__pycache__", "chroma_db", ".venv",
}


def index_codebase() -> dict:
    """
    Index backend/ and frontend/src/ into Chroma collection 'codebase'.
    Returns stats dict.
    """
    collection = _get_codebase_collection()
    model = get_embedding_model()
    upload_time = datetime.now(timezone.utc).isoformat()

    files = _iter_code_files()
    if not files:
        return {"files": 0, "chunks": 0, "message": "No code files found to index."}

    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict] = []

    for file_path in files:
        try:
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("Skip %s: %s", file_path, exc)
            continue

        if not content.strip():
            continue

        chunks = chunk_text(content)
        for idx, chunk in enumerate(chunks):
            ids.append(str(uuid.uuid4()))
            documents.append(chunk)
            embeddings.append(model.encode(chunk).tolist())
            metadatas.append({
                "filepath": rel_path,
                "chunk_index": idx,
                "upload_time": upload_time,
                "source": "codebase",
            })

    if not ids:
        return {"files": len(files), "chunks": 0, "message": "No chunks produced."}

    # Clear old codebase index before re-indexing
    try:
        _get_client().delete_collection(CODEBASE_COLLECTION)
    except Exception:
        pass
    collection = _get_codebase_collection()

    # Batch add in chunks of 100
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    logger.info("Indexed %s files, %s chunks", len(files), len(ids))
    return {
        "files": len(files),
        "chunks": len(ids),
        "message": f"Indexed {len(files)} files ({len(ids)} chunks).",
    }


def search_codebase(query: str, n_results: int = 5) -> list[dict]:
    """Semantic search over indexed codebase."""
    collection = _get_codebase_collection()

    try:
        count = collection.count()
    except Exception:
        count = 0

    if count == 0:
        return []

    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, count),
        include=["documents", "metadatas", "distances"],
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output = []
    for doc, meta, dist in zip(docs, metas, distances):
        output.append({
            "text": doc,
            "metadata": meta or {},
            "distance": dist,
        })
    return output
