"""Clean baseline schema with full foreign keys and reference lookup tables.

Revision ID: 20261013_0001_clean_architecture
Revises: None
Create Date: 2026-10-13 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20261013_0001_clean_architecture"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create clean relational schema with foreign keys and seed data."""
    # 0. Ensure extensions exist
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. ats_provider (Reference Lookup Table)
    op.create_table(
        "ats_provider",
        sa.Column("code", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("api_base_url", sa.String(length=255), nullable=True),
        sa.Column(
            "auth_type",
            sa.String(length=50),
            server_default="public_api",
            nullable=False,
        ),
        sa.Column(
            "default_rate_limit_rps",
            sa.Float(),
            server_default="5.0",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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

    # Seed ats_provider
    op.execute(
        """
        INSERT INTO ats_provider (code, name, api_base_url, default_rate_limit_rps) VALUES
            ('greenhouse', 'Greenhouse Software', 'https://boards-api.greenhouse.io/v1/boards', 5.0),
            ('lever', 'Lever Hire', 'https://api.lever.co/v0/postings', 2.0),
            ('ashby', 'Ashby HQ', 'https://api.ashbyhq.com/posting-api/job-board', 3.0),
            ('workable', 'Workable', 'https://apply.workable.com/api/v3/accounts', 2.0),
            ('custom', 'Custom Employer Portal', NULL, 1.0)
        ON CONFLICT (code) DO NOTHING;
        """
    )

    # 2. industry_sector (Taxonomy Lookup Table)
    op.create_table(
        "industry_sector",
        sa.Column("code", sa.String(length=100), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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

    # Seed industry_sector (strict snake_case, no slashes)
    op.execute(
        """
        INSERT INTO industry_sector (code, name) VALUES
            ('hft_quant_trading', 'High-Frequency & Quantitative Trading'),
            ('fintech', 'Financial Technology & Payments'),
            ('healthtech', 'Healthcare & Clinical Systems'),
            ('biotech', 'Life Sciences & Computational Biology'),
            ('ai_ml_infra', 'AI, ML & Compute Infrastructure'),
            ('ai_machine_learning', 'Artificial Intelligence & Machine Learning'),
            ('blockchain_web3', 'Blockchain, Crypto & Web3'),
            ('devtools', 'Developer Tools & Engineering Platforms'),
            ('devops_infra', 'DevOps & Cloud Infrastructure'),
            ('cybersecurity', 'Information Security & Cryptography'),
            ('enterprise_saas', 'Enterprise Software & Collaboration'),
            ('cleantech_climate', 'Clean Energy & Climate Technology'),
            ('ecommerce_retail', 'Commerce Platforms & Logistics'),
            ('gaming_entertainment', 'Interactive Media & Audio'),
            ('aerospace_defense', 'Aerospace, Defense & SpaceTech'),
            ('hardware_iot', 'Hardware, Semiconductors & Robotics'),
            ('proptech', 'Real Estate & Property Technology'),
            ('edtech', 'Educational Technology & Learning'),
            ('legaltech', 'Legal Intelligence & Compliance')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    # 3. user_profile
    op.create_table(
        "user_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "visa_status",
            sa.String(length=100),
            server_default="None",
            nullable=False,
        ),
        sa.Column(
            "remote_preference",
            sa.String(length=50),
            server_default="Remote",
            nullable=False,
        ),
        sa.Column(
            "tone_directives",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "target_roles",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column(
            "target_locations",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
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
    )
    op.create_index("ix_user_profile_email", "user_profile", ["email"], unique=True)

    # 4. cv_block
    op.create_table(
        "cv_block",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profile.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "metrics", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False
        ),
        sa.Column(
            "skills", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False
        ),
        sa.Column("embedding", Vector(1536), nullable=False),
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
    op.create_index("ix_cv_block_user_profile_id", "cv_block", ["user_profile_id"])
    op.create_index("ix_cv_block_category", "cv_block", ["category"])
    op.execute(
        "CREATE INDEX idx_cv_block_embedding_hnsw ON cv_block USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
    )

    # 5. company_dossier
    op.create_table(
        "company_dossier",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column(
            "canonical_name", sa.String(length=255), server_default="", nullable=False
        ),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column(
            "aliases", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False
        ),
        sa.Column(
            "industry",
            sa.String(length=100),
            sa.ForeignKey("industry_sector.code", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "tech_stack",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column(
            "recent_news",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("business_model", sa.Text(), nullable=True),
        sa.Column("culture_notes", sa.Text(), nullable=True),
        sa.Column(
            "data_origin",
            sa.String(length=50),
            server_default="live",
            nullable=False,
        ),
        sa.Column(
            "schema_version", sa.String(length=50), server_default="v2", nullable=False
        ),
        sa.Column(
            "field_provenance",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_refresh_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_company_dossier_company_name",
        "company_dossier",
        ["company_name"],
        unique=True,
    )
    op.create_index(
        "ix_company_dossier_canonical_name", "company_dossier", ["canonical_name"]
    )
    op.create_index("ix_company_dossier_domain", "company_dossier", ["domain"])
    op.create_index("ix_company_dossier_industry", "company_dossier", ["industry"])
    op.create_index(
        "ix_company_dossier_next_refresh_at", "company_dossier", ["next_refresh_at"]
    )

    # 6. ats_board
    op.create_table(
        "ats_board",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "provider",
            sa.String(length=50),
            sa.ForeignKey("ats_provider.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column(
            "industry",
            sa.String(length=100),
            sa.ForeignKey("industry_sector.code", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "company_dossier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("company_dossier.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("headquarters_country", sa.String(length=100), nullable=True),
        sa.Column("headquarters_country_code", sa.String(length=10), nullable=True),
        sa.Column("primary_region", sa.String(length=50), nullable=True),
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
    op.create_index("ix_ats_board_industry", "ats_board", ["industry"])
    op.create_index(
        "ix_ats_board_headquarters_country_code",
        "ats_board",
        ["headquarters_country_code"],
    )
    op.create_index("ix_ats_board_next_sync_at", "ats_board", ["next_sync_at"])

    # 7. job_listing
    op.create_table(
        "job_listing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("apply_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "ats_board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ats_board.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "ats_provider",
            sa.String(length=50),
            sa.ForeignKey("ats_provider.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ats_board_slug", sa.String(length=255), nullable=False),
        sa.Column("source_job_id", sa.String(length=255), nullable=False),
        sa.Column(
            "industry",
            sa.String(length=100),
            sa.ForeignKey("industry_sector.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "company_dossier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("company_dossier.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "raw_location",
            sa.String(length=500),
            server_default="Remote",
            nullable=False,
        ),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("state_province", sa.String(length=255), nullable=True),
        sa.Column("state_province_code", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("country_code", sa.String(length=10), nullable=True),
        sa.Column("primary_region", sa.String(length=50), nullable=True),
        sa.Column(
            "workplace_type",
            sa.String(length=50),
            server_default="on_site",
            nullable=False,
        ),
        sa.Column(
            "remote_scope",
            sa.String(length=50),
            server_default="none",
            nullable=False,
        ),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("raw_description", sa.Text(), nullable=False),
        sa.Column(
            "ats_requirements",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column("visa_sponsorship", sa.String(length=50), nullable=True),
        sa.Column("visa_notes", sa.Text(), nullable=True),
        sa.Column(
            "visa_types",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "data_origin",
            sa.String(length=50),
            server_default="live",
            nullable=False,
        ),
        sa.Column(
            "source_confidence",
            sa.String(length=50),
            server_default="high",
            nullable=False,
        ),
        sa.Column(
            "verification",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "extraction_version",
            sa.String(length=50),
            server_default="v2",
            nullable=False,
        ),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint(
            "ats_provider",
            "ats_board_slug",
            "source_job_id",
            name="uq_job_listing_provider_slug_jobid",
        ),
    )
    op.create_index("ix_job_listing_ats_board_id", "job_listing", ["ats_board_id"])
    op.create_index("ix_job_listing_ats_provider", "job_listing", ["ats_provider"])
    op.create_index("ix_job_listing_ats_board_slug", "job_listing", ["ats_board_slug"])
    op.create_index("ix_job_listing_source_job_id", "job_listing", ["source_job_id"])
    op.create_index("ix_job_listing_company_name", "job_listing", ["company_name"])
    op.create_index("ix_job_listing_title", "job_listing", ["title"])
    op.create_index("ix_job_listing_industry", "job_listing", ["industry"])
    op.create_index("ix_job_listing_city", "job_listing", ["city"])
    op.create_index(
        "ix_job_listing_state_province_code", "job_listing", ["state_province_code"]
    )
    op.create_index("ix_job_listing_country_code", "job_listing", ["country_code"])
    op.create_index("ix_job_listing_workplace_type", "job_listing", ["workplace_type"])
    op.create_index("ix_job_listing_remote_scope", "job_listing", ["remote_scope"])
    op.create_index(
        "ix_job_listing_visa_sponsorship", "job_listing", ["visa_sponsorship"]
    )
    op.create_index("ix_job_listing_status", "job_listing", ["status"])
    op.create_index("ix_job_listing_fingerprint", "job_listing", ["fingerprint"])

    # 8. application
    op.create_table(
        "application",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profile.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "job_listing_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_listing.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="saved",
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "custom_metadata",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
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
    )
    op.create_index(
        "ix_application_user_profile_id", "application", ["user_profile_id"]
    )
    op.create_index("ix_application_job_listing_id", "application", ["job_listing_id"])
    op.create_index("ix_application_status", "application", ["status"])

    # 9. feedback_log
    op.create_table(
        "feedback_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profile.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("thread_id", sa.String(length=255), nullable=False),
        sa.Column("user_feedback", sa.Text(), nullable=False),
        sa.Column(
            "prompt_weight_adjustments",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
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
    )
    op.create_index(
        "ix_feedback_log_user_profile_id", "feedback_log", ["user_profile_id"]
    )
    op.create_index("ix_feedback_log_thread_id", "feedback_log", ["thread_id"])

    # 10. ingestion_run
    op.create_table(
        "ingestion_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ats_board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ats_board.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "ats_provider",
            sa.String(length=50),
            sa.ForeignKey("ats_provider.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("board_slug", sa.String(length=255), nullable=False),
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
    op.create_index("ix_ingestion_run_ats_board_id", "ingestion_run", ["ats_board_id"])
    op.create_index("ix_ingestion_run_ats_provider", "ingestion_run", ["ats_provider"])
    op.create_index("ix_ingestion_run_board_slug", "ingestion_run", ["board_slug"])

    # 11. ingestion_task
    op.create_table(
        "ingestion_task",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column(
            "ats_board_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ats_board.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "ats_provider",
            sa.String(length=50),
            sa.ForeignKey("ats_provider.code", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("board_slug", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "payload",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
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
    op.create_index(
        "ix_ingestion_task_dedupe_key", "ingestion_task", ["dedupe_key"], unique=True
    )
    op.create_index("ix_ingestion_task_task_type", "ingestion_task", ["task_type"])
    op.create_index("ix_ingestion_task_status", "ingestion_task", ["status"])
    op.create_index("ix_ingestion_task_priority", "ingestion_task", ["priority"])
    op.create_index(
        "ix_ingestion_task_scheduled_for", "ingestion_task", ["scheduled_for"]
    )
    op.create_index(
        "ix_ingestion_task_locked_until", "ingestion_task", ["locked_until"]
    )
    op.create_index(
        "ix_ingestion_task_ats_board_id", "ingestion_task", ["ats_board_id"]
    )

    # 12. provider_usage
    op.create_table(
        "provider_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "provider",
            sa.String(length=50),
            sa.ForeignKey("ats_provider.code", ondelete="RESTRICT"),
            nullable=False,
        ),
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

    # 13. provider_state
    op.create_table(
        "provider_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "provider",
            sa.String(length=50),
            sa.ForeignKey("ats_provider.code", ondelete="RESTRICT"),
            nullable=False,
        ),
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


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("provider_state")
    op.drop_table("provider_usage")
    op.drop_table("ingestion_task")
    op.drop_table("ingestion_run")
    op.drop_table("feedback_log")
    op.drop_table("application")
    op.drop_table("job_listing")
    op.drop_table("ats_board")
    op.drop_table("company_dossier")
    op.drop_table("cv_block")
    op.drop_table("user_profile")
    op.drop_table("industry_sector")
    op.drop_table("ats_provider")
