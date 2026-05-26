"""
Application settings loaded from environment variables and .env file.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
# project root (ollama-chatbot/)
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Central configuration for the Agentic AI backend."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    @property
    def ollama_generate_url(self) -> str:
        return f"{self.ollama_base_url.rstrip('/')}/api/generate"

    # Storage paths (absolute paths)
    chroma_path: str = Field(
        default_factory=lambda: str(BACKEND_DIR / "chroma_db")
    )
    upload_dir: str = Field(
        default_factory=lambda: str(BACKEND_DIR / "uploads")
    )
    allowed_fs_root: str = Field(
        default_factory=lambda: str(PROJECT_ROOT)
    )

    # Limits
    max_upload_mb: int = 25
    max_file_read_bytes: int = 500_000

    # Agent
    agent_max_iterations: int = 10
    use_langgraph_agent: bool = True
    memory_recent_limit: int = 5

    # Codebase indexing (comma-separated relative paths from project root)
    codebase_paths: str = "backend,frontend/src"

    # Wave 3 — shell tool (restricted subprocess; enable only in trusted environments)
    enable_shell_tool: bool = False
    shell_timeout_seconds: int = 30

    # Wave 3 — LangSmith tracing
    langchain_tracing: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "ollama-agentic-ai"

    # CORS (comma-separated origins in .env)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def codebase_path_list(self) -> list[str]:
        return [p.strip() for p in self.codebase_paths.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

settings = Settings()
