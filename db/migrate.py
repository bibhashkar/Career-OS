#!/usr/bin/env python3
"""
Career-OS Lightweight Database Migration Runner.

Tracks executed migrations using a PostgreSQL tracking table (schema_migrations)
with SHA-256 checksum verification, atomic transaction boundaries, and CLI telemetry.

Usage:
    python db/migrate.py               # Apply all pending migrations sequentially
    python db/migrate.py --status      # Display migration status and checksum verification
    python db/migrate.py --baseline    # Mark existing migrations as applied without DDL execution
"""

import argparse
import asyncio
import hashlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

# Add project root to sys.path so we can import app settings if available
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("career_os.db.migrate")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def get_database_url() -> str:
    """Resolve database connection string from environment or app settings."""
    try:
        from app.core.config import settings

        raw_url = settings.DATABASE_URL
    except Exception:
        raw_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/career_os",
        )

    # Convert SQLAlchemy psycopg URL scheme to native psycopg DSN
    if raw_url.startswith("postgresql+psycopg://"):
        raw_url = raw_url.replace("postgresql+psycopg://", "postgresql://", 1)
    elif raw_url.startswith("postgresql+asyncpg://"):
        raw_url = raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return raw_url


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a migration file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_migration_files() -> list[Path]:
    """Discover all .sql migration files in sequential alphabetical order."""
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted([p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file()])


def ensure_tracking_table(conn: psycopg.Connection) -> None:
    """Ensure the schema_migrations tracking table exists."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                execution_time_ms INTEGER NOT NULL
            );
            """
        )
    conn.commit()


def get_applied_migrations(conn: psycopg.Connection) -> dict[str, dict[str, Any]]:
    """Retrieve all previously executed migrations keyed by version."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT version, checksum, applied_at, execution_time_ms
            FROM schema_migrations
            ORDER BY version ASC;
            """
        )
        rows = cur.fetchall()
        return {r["version"]: r for r in rows}


def show_status(conn: psycopg.Connection) -> int:
    """Print a clean CLI status report of migrations."""
    ensure_tracking_table(conn)
    applied = get_applied_migrations(conn)
    disk_files = get_migration_files()

    print("\n" + "=" * 80)
    print("📋 CAREER-OS DATABASE MIGRATION STATUS")
    print("=" * 80)
    print(f"{'Version':<35} | {'Status':<10} | {'Applied At':<20} | {'Checksum':<10}")
    print("-" * 80)

    all_versions = sorted(set(list(applied.keys()) + [p.name for p in disk_files]))
    if not all_versions:
        print("No migrations found.")
        print("=" * 80 + "\n")
        return 0

    has_tampered = False
    for v in all_versions:
        is_applied = v in applied
        disk_path = MIGRATIONS_DIR / v
        disk_exists = disk_path.exists()

        if is_applied and disk_exists:
            current_hash = calculate_checksum(disk_path)
            stored_hash = applied[v]["checksum"]
            if current_hash != stored_hash:
                status_str = "MODIFIED ⚠️"
                has_tampered = True
            else:
                status_str = "APPLIED ✅"
            applied_str = applied[v]["applied_at"].strftime("%Y-%m-%d %H:%M:%S")
            short_hash = stored_hash[:8]
        elif is_applied and not disk_exists:
            status_str = "MISSING ❓"
            applied_str = applied[v]["applied_at"].strftime("%Y-%m-%d %H:%M:%S")
            short_hash = applied[v]["checksum"][:8]
        else:
            status_str = "PENDING ⏳"
            applied_str = "-"
            short_hash = calculate_checksum(disk_path)[:8]

        print(f"{v:<35} | {status_str:<10} | {applied_str:<20} | {short_hash}")

    print("=" * 80 + "\n")
    if has_tampered:
        logger.warning(
            "One or more applied migration files have been modified on disk!"
        )
        return 1
    return 0


def baseline_migrations(conn: psycopg.Connection) -> int:
    """Mark all disk migrations as applied without executing DDL."""
    ensure_tracking_table(conn)
    applied = get_applied_migrations(conn)
    disk_files = get_migration_files()

    count = 0
    with conn.cursor() as cur:
        for file_path in disk_files:
            v = file_path.name
            if v not in applied:
                checksum = calculate_checksum(file_path)
                cur.execute(
                    """
                    INSERT INTO schema_migrations (version, checksum, execution_time_ms)
                    VALUES (%s, %s, %s);
                    """,
                    (v, checksum, 0),
                )
                logger.info("Baselined migration: %s (checksum: %s)", v, checksum[:8])
                count += 1
    conn.commit()
    logger.info("Baselining complete: %d migration(s) marked as applied.", count)
    return 0


def apply_migrations(conn: psycopg.Connection) -> int:
    """Apply all pending migrations inside isolated atomic transactions."""
    ensure_tracking_table(conn)
    applied = get_applied_migrations(conn)
    disk_files = get_migration_files()

    # Integrity verification of previously applied migrations
    for file_path in disk_files:
        v = file_path.name
        if v in applied:
            current_hash = calculate_checksum(file_path)
            stored_hash = applied[v]["checksum"]
            if current_hash != stored_hash:
                logger.error(
                    "Integrity Error: Migration '%s' was already applied, but disk contents changed! "
                    "Expected %s, found %s.",
                    v,
                    stored_hash,
                    current_hash,
                )
                return 1

    pending = [p for p in disk_files if p.name not in applied]
    if not pending:
        logger.info("Database is up to date. Zero pending migrations.")
        return 0

    logger.info("Discovered %d pending migration(s) to apply.", len(pending))
    for file_path in pending:
        v = file_path.name
        logger.info("Applying migration: %s...", v)
        sql_content = file_path.read_text(encoding="utf-8")
        checksum = calculate_checksum(file_path)

        start_time = time.perf_counter()
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(sql_content)
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    cur.execute(
                        """
                        INSERT INTO schema_migrations (version, checksum, execution_time_ms)
                        VALUES (%s, %s, %s);
                        """,
                        (v, checksum, duration_ms),
                    )
            logger.info("✅ Applied '%s' successfully in %d ms.", v, duration_ms)
        except Exception as exc:
            logger.error(
                "❌ Migration '%s' failed! Rolling back transaction. Error: %s",
                v,
                exc,
            )
            return 1

    logger.info("All migrations completed successfully.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Career-OS Database Migration Runner")
    parser.add_argument(
        "--status", action="store_true", help="Display migration execution status"
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Mark existing migrations as applied without executing DDL",
    )
    args = parser.parse_args()

    db_url = get_database_url()
    try:
        with psycopg.connect(db_url) as conn:
            if args.status:
                return show_status(conn)
            elif args.baseline:
                return baseline_migrations(conn)
            else:
                return apply_migrations(conn)
    except psycopg.OperationalError as exc:
        logger.error("Could not connect to PostgreSQL database (%s): %s", db_url, exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected error during migration run: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
