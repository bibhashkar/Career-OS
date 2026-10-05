"""Initial schema with pgvector extension and HNSW index.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-04 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create pgvector extension, initial relational tables, and HNSW index."""
    # Step 1: Install vector extension for semantic retrieval
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Step 2: Create user_profile table
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

    # Step 3: Create company_dossier table
    op.create_table(
        "company_dossier",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
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

    # Step 4: Create job_listing table
    op.create_table(
        "job_listing",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column(
            "location",
            sa.String(length=255),
            server_default="Remote",
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
        sa.Column(
            "company_dossier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("company_dossier.id", ondelete="RESTRICT"),
            nullable=True,
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
    op.create_index("ix_job_listing_title", "job_listing", ["title"])
    op.create_index("ix_job_listing_company_name", "job_listing", ["company_name"])
    op.create_index(
        "ix_job_listing_company_dossier_id",
        "job_listing",
        ["company_dossier_id"],
    )

    # Step 5: Create cv_block table with Vector column
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
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "metrics",
            sa.JSON(),
            server_default=sa.text("'{}'::json"),
            nullable=False,
        ),
        sa.Column(
            "skills",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(1536), nullable=True),
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

    # Step 6: Create HNSW approximate nearest-neighbour index on cv_block embedding
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cv_block_embedding_hnsw "
        "ON cv_block USING hnsw (embedding vector_cosine_ops);"
    )

    # Step 7: Create feedback_log table
    op.create_table(
        "feedback_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
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
    op.create_index("ix_feedback_log_thread_id", "feedback_log", ["thread_id"])


def downgrade() -> None:
    """Drop relational tables, indexes, and vector extension in reverse order."""
    op.execute("DROP INDEX IF EXISTS ix_cv_block_embedding_hnsw;")
    op.drop_table("feedback_log")
    op.drop_table("cv_block")
    op.drop_table("job_listing")
    op.drop_table("company_dossier")
    op.drop_table("user_profile")
    op.execute("DROP EXTENSION IF EXISTS vector;")
