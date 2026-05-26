"""PDF text extraction with per-page support for metadata."""

from pathlib import Path

from pypdf import PdfReader

from core.logging_config import get_logger

logger = get_logger("rag")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF (backward-compatible flat string).
    """
    pages = extract_pages_from_pdf(pdf_path)
    return "\n\n".join(p["text"] for p in pages)


def extract_pages_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text per page.

    Returns list of {"page": int, "text": str}.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(path))
    pages: list[dict] = []

    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": index + 1, "text": text})

    if not pages:
        logger.warning("No extractable text in PDF: %s", pdf_path)
    else:
        logger.info("Extracted %s pages from %s", len(pages), path.name)

    return pages
