"""Text chunking with overlap for RAG."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.logging_config import get_logger

logger = get_logger("rag")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_text(text: str) -> list[str]:
    """
    Split plain text into chunks (backward-compatible API).
    """
    if not text or not text.strip():
        return []
    chunks = _splitter.split_text(text)
    logger.info("Split text into %s chunks", len(chunks))
    return chunks


def chunk_pages(
    pages: list[dict],
    filename: str,
    upload_time: str,
) -> list[dict]:
    """
    Chunk per-page text and attach metadata.

    Returns list of dicts:
      text, page, chunk_index, filename, upload_time, source
    """
    all_chunks: list[dict] = []
    global_index = 0

    for page_data in pages:
        page_num = page_data["page"]
        page_chunks = _splitter.split_text(page_data["text"])

        for local_index, chunk in enumerate(page_chunks):
            all_chunks.append({
                "text": chunk,
                "page": page_num,
                "chunk_index": global_index,
                "local_chunk_index": local_index,
                "filename": filename,
                "upload_time": upload_time,
                "source": "pdf",
            })
            global_index += 1

    logger.info(
        "Chunked PDF '%s' into %s chunks (size=%s, overlap=%s)",
        filename,
        len(all_chunks),
        CHUNK_SIZE,
        CHUNK_OVERLAP,
    )
    return all_chunks
