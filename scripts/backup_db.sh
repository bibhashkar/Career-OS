#!/usr/bin/env bash
# ==============================================================================
# Career-OS PostgreSQL + pgvector Automated Backup & Snapshot Utility
#
# Usage:
#   ./scripts/backup_db.sh [backup_directory]
#
# Defaults:
#   backup_directory: ./backups
#
# Environment variables:
#   POSTGRES_HOST     (default: localhost)
#   POSTGRES_PORT     (default: 5432)
#   POSTGRES_DB       (default: career_os)
#   POSTGRES_USER     (default: postgres)
#   POSTGRES_PASSWORD (optional, or passed via .pgpass / PGPASSWORD)
#   BACKUP_RETENTION_DAYS (default: 7)
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-career_os}"
DB_USER="${POSTGRES_USER:-postgres}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

mkdir -p "${BACKUP_DIR}"

BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.sql.gz"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting PostgreSQL backup for database: '${DB_NAME}'"
echo "  Target Host: ${DB_HOST}:${DB_PORT}"
echo "  Target User: ${DB_USER}"
echo "  Destination: ${BACKUP_FILE}"

if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "career_os_postgres"; then
    echo "  Detected running Docker container 'career_os_postgres'. Running pg_dump via docker exec..."
    docker exec -t career_os_postgres pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists | gzip -9 > "${BACKUP_FILE}"
elif command -v pg_dump >/dev/null 2>&1; then
    echo "  Running local pg_dump..."
    PGHOST="${DB_HOST}" PGPORT="${DB_PORT}" PGUSER="${DB_USER}" PGDATABASE="${DB_NAME}" pg_dump --clean --if-exists | gzip -9 > "${BACKUP_FILE}"
else
    echo "ERROR: Neither 'pg_dump' nor a running 'career_os_postgres' Docker container was found." >&2
    exit 1
fi

FILE_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completed successfully! (Size: ${FILE_SIZE})"

# Prune snapshots older than RETENTION_DAYS
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pruning backups older than ${RETENTION_DAYS} days in ${BACKUP_DIR}..."
find "${BACKUP_DIR}" -type f -name "${DB_NAME}_backup_*.sql.gz" -mtime +"${RETENTION_DAYS}" -exec rm -f {} +
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup & retention cycle completed."
