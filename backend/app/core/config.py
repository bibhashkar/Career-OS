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
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings resolved from environment variables.

    Fields map 1-to-1 with environment variable names (case-insensitive).
    All fields have safe local-development defaults so new engineers can run
    the stack without creating a .env file from scratch.
    """

    model_config = SettingsConfigDict(
        # Load .env from the directory where the server is launched (backend/).
        env_file=".env",
        env_file_encoding="utf-8",
        # Silently ignore extra env vars — useful when the shell exports
        # variables consumed by other tools (Docker, poetry, etc.).
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application identity ----
    APP_NAME: str = "Career-OS"
    APP_ENV: str = "development"
    # When True, SQLAlchemy echoes every SQL statement — disable in production.
    APP_DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # ---- PostgreSQL connection ----
    # DATABASE_URL is the primary connection string used by SQLAlchemy.
    # The individual POSTGRES_* fields are provided as a convenience for
    # operators who prefer constructing connection strings from parts via
    # docker-compose environment blocks.
    POSTGRES_DB: str = "career_os"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/career_os"
    )

    # ---- CORS allowed origins ----
    # Defaults to the two ports used by the local Vite dev server.
    # In production, replace with the exact deployed frontend domain.
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ---- External API keys (all optional for local/mock development) ----
    # The agent tools implement hermetic offline fallbacks so the full pipeline
    # runs in CI without these keys. Set them to enable live data sources.
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    # JSearch (RapidAPI) — live job board search
    JSEARCH_API_KEY: str | None = None
    # Exa — neural web search for company intelligence
    EXA_API_KEY: str | None = None
    # Apollo — company and contact enrichment
    APOLLO_API_KEY: str | None = None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """
        Normalise CORS_ORIGINS from multiple env-variable formats.

        Docker Compose and many CI systems pass list-type settings as either
        a JSON array string (``["http://a.com","http://b.com"]``) or a
        comma-separated string (``http://a.com,http://b.com``). This validator
        handles both so operators don't need to choose one format.
        """
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Module-level singleton — imported throughout the app as:
#   ``from app.core.config import settings``
settings = Settings()
