"""
Application settings loaded from environment variables and .env file.
"""

from pathlib import Path

from pydantic import AliasChoices, Field
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
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("OLLAMA_URL"),
    )
    ollama_model: str = Field(
        default="llama3",
        validation_alias=AliasChoices("OLLAMA_MODEL", "MODEL_NAME"),
    )

    @property
    def ollama_generate_url(self) -> str:
        return f"{self.ollama_base_url.rstrip('/')}/api/generate"

    # Storage paths (absolute paths)
    chroma_path: str = Field(
        default_factory=lambda: str(BACKEND_DIR / "chroma_db"),
        validation_alias=AliasChoices("CHROMA_PATH"),
    )
    upload_dir: str = Field(
        default_factory=lambda: str(BACKEND_DIR / "uploads"),
        validation_alias=AliasChoices("UPLOAD_DIR"),
    )
    allowed_fs_root: str = Field(
        default_factory=lambda: str(PROJECT_ROOT),
        validation_alias=AliasChoices("ALLOWED_FS_ROOT"),
    )

    # Limits
    max_upload_mb: int = Field(default=25, validation_alias=AliasChoices("MAX_UPLOAD_MB"))
    # Maximum bytes to read from files via file tools (default 500k)
    max_file_read_bytes: int = Field(default=500_000, validation_alias=AliasChoices("MAX_FILE_SIZE"))

    # Agent
    agent_max_iterations: int = 10
    use_langgraph_agent: bool = True
    # Use the built-in agentic loop (Thought->Action->Observation)
    use_agentic_loop: bool = Field(default=True, validation_alias=AliasChoices("USE_AGENTIC_LOOP"))
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
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("CORS_ORIGINS"),
    )

    # MVP integrations
    google_sheets_id: str = Field(default="", validation_alias=AliasChoices("GOOGLE_SHEETS_ID"))
    google_service_account_path: str = Field(default="", validation_alias=AliasChoices("GOOGLE_SERVICE_ACCOUNT_PATH"))
    n8n_webhook_url: str = Field(default="", validation_alias=AliasChoices("N8N_WEBHOOK_URL"))
    application_memory_path: str = Field(
        default_factory=lambda: str(BACKEND_DIR / "memory" / "application_memory.json"),
        validation_alias=AliasChoices("APPLICATION_MEMORY_PATH"),
    )

    # Database (SQLite) — file path or full URL
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{BACKEND_DIR / 'data' / 'app.db'}",
        validation_alias=AliasChoices("DATABASE_URL"),
    )

    @property
    def codebase_path_list(self) -> list[str]:
        return [p.strip() for p in self.codebase_paths.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

settings = Settings()
