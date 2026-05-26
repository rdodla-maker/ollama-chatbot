"""
Persistent agent memory with recent-task recall and semantic search.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from core.config import settings
from core.logging_config import get_logger
from rag.embeddings import get_embedding_model

logger = get_logger("agent")

MEMORY_FILE = Path(settings.upload_dir).parent / "agent_memory.json"
# Prefer backend/agent_memory.json if it exists (Wave 1 location)
_LEGACY_MEMORY = Path(__file__).resolve().parent.parent / "agent_memory.json"


class MemoryStore:
    """Read/write agent_memory.json with retrieval helpers."""

    def __init__(self, path: Path | None = None):
        if path is None:
            path = _LEGACY_MEMORY if _LEGACY_MEMORY.exists() else MEMORY_FILE
        self.path = path
        self.entries: list[dict] = self._load()

    def _load(self) -> list:
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load memory file: %s", exc)
            return []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2)

    def append(self, task: str, plan: str, result: str) -> None:
        self.entries.append({
            "task": task,
            "plan": plan,
            "result": result[:2000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep file from growing forever in dev
        if len(self.entries) > 200:
            self.entries = self.entries[-200:]
        self._save()
        logger.info("Saved memory entry (%s total)", len(self.entries))

    def get_recent(self, limit: int | None = None) -> list[dict]:
        n = limit or settings.memory_recent_limit
        return self.entries[-n:]

    def get_context_for_query(self, query: str) -> str:
        """
        Build a memory block from recent tasks + semantically similar past tasks.
        """
        if not self.entries:
            return "No prior tasks in memory."

        parts: list[str] = []
        recent = self.get_recent()
        parts.append("Recent tasks:")
        for entry in recent:
            parts.append(
                f"- Task: {entry.get('task', '')}\n"
                f"  Result: {str(entry.get('result', ''))[:300]}"
            )

        similar = self._semantic_search(query, top_k=3)
        if similar:
            parts.append("\nRelevant past tasks:")
            for entry in similar:
                if entry not in recent:
                    parts.append(
                        f"- Task: {entry.get('task', '')}\n"
                        f"  Result: {str(entry.get('result', ''))[:300]}"
                    )

        return "\n".join(parts)

    def _semantic_search(self, query: str, top_k: int = 3) -> list[dict]:
        if len(self.entries) < 2:
            return []

        try:
            model = get_embedding_model()
            query_vec = model.encode(query)
            scored: list[tuple[float, dict]] = []

            for entry in self.entries[:-settings.memory_recent_limit]:
                text = f"{entry.get('task', '')} {entry.get('result', '')}"
                if not text.strip():
                    continue
                vec = model.encode(text)
                sim = float(np.dot(query_vec, vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-9
                ))
                scored.append((sim, entry))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [e for _, e in scored[:top_k]]
        except Exception as exc:
            logger.warning("Semantic memory search failed: %s", exc)
            return []


memory_store = MemoryStore()
