"""ChromaDB vector storage and semantic search for PDF chunks."""

import uuid
from datetime import datetime, timezone

import chromadb

from core.config import settings
from core.logging_config import get_logger
from rag.chunking import chunk_pages
from rag.embeddings import get_embedding_model
from rag.pdf_loader import extract_pages_from_pdf

logger = get_logger("rag")

_chroma_client: chromadb.PersistentClient | None = None
_collection = None

COLLECTION_NAME = "pdf_docs"


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_path)
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME
        )
        logger.info("ChromaDB ready at %s", settings.chroma_path)
    return _collection


def store_embeddings(chunks: list) -> str:
    """
    Store text chunks in ChromaDB.

    Accepts:
      - list[str] (legacy) — stores with minimal metadata
      - list[dict] with text + metadata (preferred)

    Returns document_id for the upload batch.
    """
    if not chunks:
        logger.warning("store_embeddings called with empty chunks")
        return ""

    collection = _get_collection()
    model = get_embedding_model()
    document_id = str(uuid.uuid4())

    ids: list[str] = []
    documents: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict] = []

    for item in chunks:
        if isinstance(item, str):
            chunk_id = str(uuid.uuid4())
            text = item
            meta = {
                "document_id": document_id,
                "chunk_index": len(ids),
                "source": "pdf",
                "filename": "unknown",
                "upload_time": datetime.now(timezone.utc).isoformat(),
            }
        else:
            text = item["text"]
            chunk_id = str(uuid.uuid4())
            meta = {
                "document_id": document_id,
                "chunk_index": item.get("chunk_index", len(ids)),
                "page": item.get("page", 0),
                "filename": item.get("filename", "unknown"),
                "upload_time": item.get("upload_time", ""),
                "source": item.get("source", "pdf"),
            }

        ids.append(chunk_id)
        documents.append(text)
        embeddings.append(model.encode(text).tolist())
        metadatas.append(meta)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info(
        "Stored %s chunks for document_id=%s", len(ids), document_id
    )
    return document_id


def ingest_pdf(pdf_path: str, filename: str) -> tuple[int, str]:
    """
    Full ingest pipeline: extract pages → chunk → embed → store.

    Returns (chunk_count, document_id).
    """
    upload_time = datetime.now(timezone.utc).isoformat()
    pages = extract_pages_from_pdf(pdf_path)

    if not pages:
        raise ValueError(
            "Could not extract text from PDF. "
            "The file may be scanned images or empty."
        )

    chunks = chunk_pages(pages, filename=filename, upload_time=upload_time)
    document_id = store_embeddings(chunks)
    return len(chunks), document_id


def search_chunks(query: str, n_results: int = 3) -> list[str]:
    """
    Semantic search — returns chunk text strings (backward-compatible).

    Returns empty list when collection is empty or no matches.
    """
    collection = _get_collection()

    try:
        count = collection.count()
    except Exception:
        count = 0

    if count == 0:
        logger.info("Chroma collection empty — no PDFs indexed yet")
        return []

    model = get_embedding_model()
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, count),
    )

    documents = results.get("documents") or [[]]
    if not documents or not documents[0]:
        logger.info("No matching chunks for query")
        return []

    logger.info("Found %s relevant chunks", len(documents[0]))
    return documents[0]


def search_chunks_with_metadata(
    query: str,
    n_results: int = 3,
) -> list[dict]:
    """Search with metadata for richer API responses."""
    collection = _get_collection()

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

    if not docs:
        return []

    output = []
    for doc, meta, dist in zip(docs, metas, distances):
        output.append({
            "text": doc,
            "metadata": meta or {},
            "distance": dist,
        })
    return output
