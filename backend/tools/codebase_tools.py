"""Codebase search and analysis tools."""

from core.config import PROJECT_ROOT
from core.logging_config import get_logger
from rag.codebase_index import search_codebase

logger = get_logger("tools")


def codebase_search_tool(query: str) -> str:
    """Search indexed project source code."""
    try:
        results = search_codebase(query, n_results=5)
        if not results:
            return (
                "No codebase index found. "
                "Ask the API to POST /index-codebase first."
            )
        parts = []
        for r in results:
            meta = r.get("metadata", {})
            path = meta.get("filepath", "unknown")
            parts.append(f"[{path}]\n{r['text']}")
        logger.info("Codebase search returned %s hits", len(parts))
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        logger.warning("Codebase search error: %s", e)
        return f"Error: {str(e)}"


def analyze_repository_tool(_query: str = "") -> str:
    """Summarize project structure, APIs, and dependencies."""
    from tools.file_tools import folder_scanner_tool

    backend = str(PROJECT_ROOT / "backend")
    frontend = str(PROJECT_ROOT / "frontend")

    structure = folder_scanner_tool(backend)
    fe_structure = folder_scanner_tool(frontend)

    # Read key manifests
    hints = []
    for rel in ("requirements.txt", "frontend/package.json", "README.md"):
        p = PROJECT_ROOT / rel
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")[:1500]
                hints.append(f"=== {rel} ===\n{text}")
            except OSError:
                pass

    return (
        "Project structure (backend):\n"
        f"{structure[:8000]}\n\n"
        "Project structure (frontend):\n"
        f"{fe_structure[:4000]}\n\n"
        + "\n".join(hints)
    )
