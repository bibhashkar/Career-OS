"""Unit tests for Pydantic Settings configuration and validation."""

import pytest

from app.core.config import Settings


def test_settings_default_debug_is_false() -> None:
    """Verify APP_DEBUG defaults to False for security and clean logs."""
    config = Settings(_env_file=None)
    assert config.APP_DEBUG is False


def test_settings_workflow_thresholds() -> None:
    """Verify workflow constants are properly defined in Settings."""
    config = Settings()
    assert config.ATS_PASS_THRESHOLD == 75.0
    assert config.MAX_REVISIONS == 3


def test_settings_derives_database_url_from_postgres_parts() -> None:
    """Verify DATABASE_URL is dynamically assembled from POSTGRES_* attributes."""
    config = Settings(
        POSTGRES_USER="career_user",
        POSTGRES_PASSWORD="secure_password",
        POSTGRES_HOST="db.internal",
        POSTGRES_PORT=5433,
        POSTGRES_DB="custom_career_os",
        DATABASE_URL="",
    )
    expected_url = (
        "postgresql+psycopg://career_user:secure_password@db.internal:5433/"
        "custom_career_os"
    )
    assert config.DATABASE_URL == expected_url


def test_settings_custom_database_url_precedence() -> None:
    """Verify caller-provided DATABASE_URL takes precedence over components."""
    custom_url = "postgresql+psycopg://custom:secret@remote.host:5432/db"
    config = Settings(DATABASE_URL=custom_url)
    assert config.DATABASE_URL == custom_url


def test_settings_production_blocks_localhost_database() -> None:
    """Verify production mode rejects localhost database connection strings."""
    with pytest.raises(ValueError, match="cannot point to localhost in production"):
        Settings(
            APP_ENV="production",
            POSTGRES_HOST="localhost",
            DATABASE_URL="",
        )


def test_settings_production_blocks_debug_mode() -> None:
    """Verify production mode rejects APP_DEBUG=True."""
    with pytest.raises(ValueError, match="APP_DEBUG must be False in production"):
        Settings(
            APP_ENV="production",
            APP_DEBUG=True,
            POSTGRES_HOST="remote.db.provider",
            DATABASE_URL="",
        )
