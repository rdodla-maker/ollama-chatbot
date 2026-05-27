"""Resume parsing helpers for PDF and DOCX uploads."""
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger("resume_parser")

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - fallback if library missing
    PdfReader = None

try:
    from docx import Document
except Exception:  # pragma: no cover
    Document = None


def parse_pdf(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed")
    text_parts = []
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        logger.exception("Failed to open PDF: %s", exc)
        raise

    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            text_parts.append(text)
    result = "\n\n".join(text_parts)
    if not result:
        # Try a fallback: read raw bytes and attempt best-effort decode
        try:
            raw = path.read_bytes()
            result = raw.decode("utf-8", errors="ignore")[:20000]
        except Exception:
            result = ""
    return result


def parse_docx(path: Path) -> str:
    if Document is None:
        raise RuntimeError("python-docx is not installed")
    try:
        doc = Document(str(path))
        parts = [p.text for p in doc.paragraphs if p.text]
        return "\n".join(parts)
    except Exception as exc:
        logger.exception("Failed to parse DOCX: %s", exc)
        # fallback to raw bytes
        try:
            raw = path.read_bytes()
            return raw.decode("utf-8", errors="ignore")[:20000]
        except Exception:
            return ""


def extract_text_from_resume(path: str) -> Tuple[str, str]:
    """Return tuple (text, file_type) where file_type is 'pdf' or 'docx'."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(p), "pdf"
    if suffix in (".docx", ".doc"):
        return parse_docx(p), "docx"
    raise ValueError("Unsupported resume file type: " + suffix)
