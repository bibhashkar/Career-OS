"""
Application configuration via Pydantic BaseSettings.

All runtime configuration is loaded from environment variables (or a .env file
for local development). Using Pydantic BaseSettings ensures:
  - Every setting has an explicit type, default, and validation rule.
  - Missing required secrets are caught at startup, not at request time.
  - The same Settings class works in all environments by swapping .env files.

Important: the ``settings`` singleton is instantiated at module import time so
that any misconfiguration fails fast during application startup rather than
silently at the first request that needs the value.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine directory paths for robust .env loading across execution contexts
_CORE_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _CORE_DIR.parent.parent
_PROJECT_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    """
    Global application settings resolved from environment variables.

    Fields map 1-to-1 with environment variable names (case-insensitive).
    All fields have safe local-development defaults so new engineers can run
    the stack without creating a .env file from scratch.
    """

    model_config = SettingsConfigDict(
        # Look for .env first at the repository root, then backend/, then cwd.
        # This guarantees that launching from root, backend/, or container
        # subdirectories loads values from .env directly without fallback.
        env_file=(
            str(_PROJECT_ROOT / ".env"),
            str(_BACKEND_DIR / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        # Silently ignore extra env vars — useful when the shell exports
        # variables consumed by other tools (Docker, poetry, etc.).
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application identity ----
    APP_NAME: str = "Career-OS"
    APP_ENV: str = "development"
    # When True, SQLAlchemy echoes every SQL statement — disabled by default
    # to avoid leaking query structure or sensitive data into application logs.
    APP_DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # ---- Workflow & ATS Thresholds ----
    ATS_PASS_THRESHOLD: float = 75.0
    MAX_REVISIONS: int = 3
    GRAPH_RECURSION_LIMIT: int = 25

    # ---- Payload & Buffer Security Limits ----
    MAX_CV_RAW_TEXT_LENGTH: int = 50000
    MAX_FEEDBACK_TEXT_LENGTH: int = 5000
    MAX_WS_FRAME_BYTES: int = 16384
    RATE_LIMIT_PER_MINUTE: int = 120
    CV_TAILOR_RATE_LIMIT_PER_MINUTE: int = 20

    # ---- Authentication & Cryptographic Keys ----
    SECRET_KEY: str = "career-os-dev-insecure-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ---- PostgreSQL connection ----
    # The individual POSTGRES_* fields configure discrete connection parameters.
    # DATABASE_URL is automatically derived from these components unless
    # an explicit custom connection string is provided.
    POSTGRES_DB: str = "career_os"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    # ---- CORS allowed origins & security policy ----
    # Defaults to the two ports used by the local Vite dev server.
    # In production, replace with the exact deployed frontend domain.
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_METHODS: list[str] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "HEAD",
    ]
    CORS_ALLOW_HEADERS: list[str] = [
        "Content-Type",
        "Authorization",
        "X-Correlation-ID",
        "Accept",
        "Origin",
    ]

    # ---- External API keys & LLM Provider (optional for mock development) ----
    # The agent nodes and tools implement hermetic offline fallbacks so the full
    # pipeline runs in CI without live API keys.
    LLM_PROVIDER: str = "gemini"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    # JSearch (RapidAPI) — live job board search
    JSEARCH_API_KEY: str | None = None
    # Exa — neural web search for company intelligence
    EXA_API_KEY: str | None = None
    # Apollo — company and contact enrichment
    APOLLO_API_KEY: str | None = None

    # ---- Ingestion rate limits & quotas (daily maximums) ----
    RATE_LIMIT_GEMINI_RPM: int = 15
    RATE_LIMIT_GEMINI_RPD: int = 1500
    RATE_LIMIT_DUCKDUCKGO_HOURLY: int = 60
    RATE_LIMIT_JOBSPY_HOURLY: int = 30
    RATE_LIMIT_GITHUB_HOURLY: int = 60

    @field_validator(
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "JSEARCH_API_KEY",
        "EXA_API_KEY",
        "APOLLO_API_KEY",
        mode="before",
    )
    @classmethod
    def blank_str_to_none(cls, v: Any) -> Any:
        """Treat blank/empty strings in .env as None for optional API keys."""
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator(
        "CORS_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before"
    )
    @classmethod
    def assemble_cors_lists(cls, v: Any) -> list[str]:
        """
        Normalise list settings from multiple env-variable formats.

        Docker Compose and many CI systems pass list-type settings as either
        a JSON array string (``["http://a.com","http://b.com"]``) or a
        comma-separated string (``http://a.com,http://b.com``). This validator
        handles both formats cleanly.
        """
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @model_validator(mode="after")
    def assemble_and_validate_settings(self) -> "Settings":
        """
        Derive DATABASE_URL from POSTGRES_* and validate production constraints.
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        if self.APP_ENV == "production":
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL cannot point to localhost in production environment."
                )
            if self.APP_DEBUG:
                raise ValueError("APP_DEBUG must be False in production.")
            if "dev-insecure" in self.SECRET_KEY:
                raise ValueError(
                    "SECRET_KEY must be securely configured in production."
                )

        return self


# Module-level singleton — imported throughout the app as:
#   ``from app.core.config import settings``
settings = Settings()
