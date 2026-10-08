"""Ingestion pipeline schema: ATS boards, tasks, ledger, state, and listing provenance.

Revision ID: 0002_ingestion_pipeline
Revises: 0001_initial_schema
Create Date: 2026-10-08 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_ingestion_pipeline"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Create ingestion subsystem tables and add provenance columns to existing tables.
    """
    # 1. Create ats_board table
    op.create_table(
        "ats_board",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("tier", sa.Integer(), server_default="1", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="5", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "consecutive_failures", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "discovered_via",
            sa.String(length=50),
            server_default="seed",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("provider", "slug", name="uq_ats_board_provider_slug"),
    )
    op.create_index("ix_ats_board_provider", "ats_board", ["provider"])
    op.create_index("ix_ats_board_slug", "ats_board", ["slug"])
    op.create_index("ix_ats_board_company_name", "ats_board", ["company_name"])
    op.create_index("ix_ats_board_next_sync_at", "ats_board", ["next_sync_at"])

    # 2. Create ingestion_run table
    op.create_table(
        "ingestion_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("board_slug", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("fetched_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("new_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("closed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ingestion_run_source", "ingestion_run", ["source"])

    # 3. Create provider_usage table (atomic quota ledger)
    op.create_table(
        "provider_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("period_key", sa.String(length=50), nullable=False),
        sa.Column("call_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_calls", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("provider", "period_key", name="uq_provider_usage_period"),
    )
    op.create_index("ix_provider_usage_provider", "provider_usage", ["provider"])
    op.create_index("ix_provider_usage_period_key", "provider_usage", ["period_key"])

    # 4. Create provider_state table (circuit breaker)
    op.create_table(
        "provider_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column(
            "is_circuit_open", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_provider_state_provider", "provider_state", ["provider"], unique=True
    )

    # 5. Create ingestion_task table (queue)
    op.create_table(
        "ingestion_task",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=50), server_default="pending", nullable=False
        ),
        sa.Column("priority", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "payload", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False
        ),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "scheduled_for",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ingestion_task_task_type", "ingestion_task", ["task_type"])
    op.create_index(
        "ix_ingestion_task_dedupe_key", "ingestion_task", ["dedupe_key"], unique=True
    )
    op.create_index("ix_ingestion_task_status", "ingestion_task", ["status"])
    op.create_index("ix_ingestion_task_priority", "ingestion_task", ["priority"])
    op.create_index(
        "ix_ingestion_task_scheduled_for", "ingestion_task", ["scheduled_for"]
    )
    op.create_index(
        "ix_ingestion_task_locked_until", "ingestion_task", ["locked_until"]
    )

    # 6. Add provenance & dedupe columns to job_listing
    op.add_column(
        "job_listing",
        sa.Column(
            "source", sa.String(length=100), server_default="legacy", nullable=False
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "source_job_id", sa.String(length=255), server_default="", nullable=False
        ),
    )
    op.add_column(
        "job_listing", sa.Column("apply_url", sa.String(length=1024), nullable=True)
    )
    op.add_column(
        "job_listing", sa.Column("fingerprint", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "job_listing", sa.Column("content_hash", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "status", sa.String(length=50), server_default="active", nullable=False
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "data_origin", sa.String(length=50), server_default="legacy", nullable=False
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "source_confidence",
            sa.String(length=50),
            server_default="high",
            nullable=False,
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "visa_sponsorship",
            sa.String(length=50),
            server_default="unknown",
            nullable=False,
        ),
    )
    op.add_column(
        "job_listing", sa.Column("remote_type", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "extraction_version",
            sa.String(length=50),
            server_default="v1",
            nullable=False,
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "verification",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "job_listing", sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "job_listing",
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_listing",
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_job_listing_source", "job_listing", ["source"])
    op.create_index("ix_job_listing_source_job_id", "job_listing", ["source_job_id"])
    op.create_index("ix_job_listing_fingerprint", "job_listing", ["fingerprint"])
    op.create_index("ix_job_listing_status", "job_listing", ["status"])
    op.create_unique_constraint(
        "uq_job_listing_source_job_id", "job_listing", ["source", "source_job_id"]
    )

    # 7. Add provenance columns to company_dossier
    op.add_column(
        "company_dossier",
        sa.Column(
            "canonical_name", sa.String(length=255), server_default="", nullable=False
        ),
    )
    op.add_column(
        "company_dossier",
        sa.Column(
            "aliases", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False
        ),
    )
    op.add_column(
        "company_dossier",
        sa.Column(
            "data_origin", sa.String(length=50), server_default="legacy", nullable=False
        ),
    )
    op.add_column(
        "company_dossier",
        sa.Column(
            "schema_version", sa.String(length=50), server_default="v1", nullable=False
        ),
    )
    op.add_column(
        "company_dossier",
        sa.Column(
            "field_provenance",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "company_dossier",
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "company_dossier",
        sa.Column("next_refresh_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_company_dossier_canonical_name", "company_dossier", ["canonical_name"]
    )
    op.create_index("ix_company_dossier_domain", "company_dossier", ["domain"])
    op.create_index(
        "ix_company_dossier_next_refresh_at", "company_dossier", ["next_refresh_at"]
    )


def downgrade() -> None:
    """Revert ingestion subsystem changes and drop added columns and tables."""
    # Revert company_dossier
    op.drop_index("ix_company_dossier_next_refresh_at", table_name="company_dossier")
    op.drop_index("ix_company_dossier_domain", table_name="company_dossier")
    op.drop_index("ix_company_dossier_canonical_name", table_name="company_dossier")
    op.drop_column("company_dossier", "next_refresh_at")
    op.drop_column("company_dossier", "last_fetched_at")
    op.drop_column("company_dossier", "field_provenance")
    op.drop_column("company_dossier", "schema_version")
    op.drop_column("company_dossier", "data_origin")
    op.drop_column("company_dossier", "aliases")
    op.drop_column("company_dossier", "canonical_name")

    # Revert job_listing
    op.drop_constraint("uq_job_listing_source_job_id", "job_listing", type_="unique")
    op.drop_index("ix_job_listing_status", table_name="job_listing")
    op.drop_index("ix_job_listing_fingerprint", table_name="job_listing")
    op.drop_index("ix_job_listing_source_job_id", table_name="job_listing")
    op.drop_index("ix_job_listing_source", table_name="job_listing")
    op.drop_column("job_listing", "last_verified_at")
    op.drop_column("job_listing", "last_fetched_at")
    op.drop_column("job_listing", "last_seen_at")
    op.drop_column("job_listing", "first_seen_at")
    op.drop_column("job_listing", "posted_at")
    op.drop_column("job_listing", "verification")
    op.drop_column("job_listing", "extraction_version")
    op.drop_column("job_listing", "remote_type")
    op.drop_column("job_listing", "visa_sponsorship")
    op.drop_column("job_listing", "source_confidence")
    op.drop_column("job_listing", "data_origin")
    op.drop_column("job_listing", "status")
    op.drop_column("job_listing", "content_hash")
    op.drop_column("job_listing", "fingerprint")
    op.drop_column("job_listing", "apply_url")
    op.drop_column("job_listing", "source_job_id")
    op.drop_column("job_listing", "source")

    # Drop tables
    op.drop_table("ingestion_task")
    op.drop_table("provider_state")
    op.drop_table("provider_usage")
    op.drop_table("ingestion_run")
    op.drop_table("ats_board")
