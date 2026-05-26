"""
Filesystem security: path allowlisting, traversal prevention, and scan filters.
"""

from pathlib import Path

from core.config import settings

# Directory names skipped during folder scans
IGNORED_DIR_NAMES = {
    "venv",
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "chroma_db",
}


def get_allowed_root() -> Path:
    """Resolved project root allowed for file/folder tools."""
    return Path(settings.allowed_fs_root).resolve()


def resolve_safe_path(user_path: str) -> Path:
    """
    Resolve a user-supplied path and ensure it stays inside ALLOWED_ROOT.
    Raises ValueError if the path escapes the allowed directory.
    """
    if not user_path or not str(user_path).strip():
        raise ValueError("Path is required.")

    allowed_root = get_allowed_root()
    raw = Path(user_path.strip())

    if raw.is_absolute():
        candidate = raw.resolve()
    else:
        candidate = (allowed_root / raw).resolve()

    try:
        candidate.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError(
            f"Access denied: path must be inside {allowed_root}"
        ) from exc

    return candidate


def is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIR_NAMES


def is_likely_binary(path: Path) -> bool:
    """Quick check for binary files before reading as text."""
    try:
        with path.open("rb") as f:
            sample = f.read(8192)
    except OSError:
        return True

    if b"\x00" in sample:
        return True

    text_ext = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt",
        ".html", ".css", ".yml", ".yaml", ".toml", ".ini", ".env",
        ".xml", ".csv", ".sql", ".sh", ".bat", ".ps1",
    }
    if path.suffix.lower() in text_ext:
        return False

    # Unknown extension with mostly non-text bytes
    if not sample:
        return False

    text_chars = sum(
        1 for b in sample if b in (9, 10, 13) or 32 <= b < 127
    )
    return text_chars / len(sample) < 0.85


def read_text_file_limited(path: Path, max_bytes: int | None = None) -> str:
    """Read a text file with a byte size cap."""
    limit = max_bytes or settings.max_file_read_bytes

    if is_likely_binary(path):
        raise ValueError(f"Binary or unsupported file type: {path.name}")

    size = path.stat().st_size
    if size > limit:
        raise ValueError(
            f"File too large ({size} bytes). Max allowed: {limit} bytes."
        )

    return path.read_text(encoding="utf-8", errors="replace")
