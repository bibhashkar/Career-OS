"""Unit tests for Career-OS pure SQL migration runner and baseline integrity."""

import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = ROOT_DIR / "db"
MIGRATIONS_DIR = DB_DIR / "migrations"
if str(DB_DIR) not in sys.path:
    sys.path.insert(0, str(DB_DIR))

import migrate  # noqa: E402


def test_migration_files_discovery_and_sequence() -> None:
    """Verify 0001_initial_schema.sql is discovered in migrations directory."""
    files = migrate.get_migration_files()
    assert len(files) >= 1
    assert files[0].name == "0001_initial_schema.sql"

    # Verify sequential naming convention: 4 digits + underscore
    for f in files:
        prefix = f.name[:4]
        assert prefix.isdigit(), f"Migration file {f.name} must start with 4 digits"
        assert f.name[4] == "_", (
            f"Migration file {f.name} must have underscore after prefix"
        )


def test_initial_schema_file_contents_and_extensions() -> None:
    """Verify 0001_initial_schema.sql contains required extensions, tables, and seeds."""
    initial_sql_path = MIGRATIONS_DIR / "0001_initial_schema.sql"
    assert initial_sql_path.exists(), "0001_initial_schema.sql not found"

    content = initial_sql_path.read_text(encoding="utf-8")
    # Verify extensions
    assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' in content
    assert "CREATE EXTENSION IF NOT EXISTS vector;" in content

    # Verify key tables exist
    expected_tables = [
        "ats_provider",
        "industry_sector",
        "user_profile",
        "cv_block",
        "company_dossier",
        "ats_board",
        "job_listing",
        "application",
        "feedback_log",
        "ingestion_run",
        "ingestion_task",
        "provider_usage",
        "provider_state",
    ]
    for table in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in content, (
            f"Missing table {table}"
        )

    # Verify key indexes and constraints
    assert "idx_cv_block_embedding_hnsw" in content
    assert "uq_job_listing_provider_slug_jobid" in content
    assert "ON DELETE RESTRICT" in content


def test_checksum_calculation() -> None:
    """Verify SHA-256 calculation matches file hash."""
    initial_sql_path = MIGRATIONS_DIR / "0001_initial_schema.sql"
    checksum = migrate.calculate_checksum(initial_sql_path)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)

    # Cross-check with manual hashlib
    with open(initial_sql_path, "rb") as f:
        expected = hashlib.sha256(f.read()).hexdigest()
    assert checksum == expected


def test_migrate_show_status_runs_cleanly() -> None:
    """Verify show_status displays cleanly with mock connection."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchall.return_value = []

    exit_code = migrate.show_status(mock_conn)
    assert exit_code == 0
