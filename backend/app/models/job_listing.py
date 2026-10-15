"""
JobListing model storing raw descriptions, requirements, and metadata.

This table records job postings discovered by crawler workers or imported by
the user. It stores raw job descriptions alongside parsed ATS criteria, fine-grained
location hierarchies, work modality, and multi-jurisdiction visa policies.

Relational Safety:
  - ``ats_board_id`` strictly references the tracked employer career board with
    ``ondelete="RESTRICT"``.
  - ``ats_provider`` references registered ATS platforms with ``ondelete="RESTRICT"``.
  - ``industry`` references standardized industry taxonomy with ``ondelete="RESTRICT"``.
  - ``company_dossier_id`` references optional deep-dive employer research.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.company_dossier import CompanyDossier
    from app.models.ingestion import ATSBoard
    from app.models.user_account import JobMatchCache


class JobListing(Base, UUIDMixin, TimestampMixin):
    """
    Stores discovered job listings, raw job descriptions, and ATS criteria.
    """

    __tablename__ = "job_listing"
    __table_args__ = (
        UniqueConstraint(
            "ats_provider",
            "ats_board_slug",
            "source_job_id",
            name="uq_job_listing_provider_slug_jobid",
        ),
    )

    # Core metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    apply_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Relational Foreign Keys
    ats_board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ats_board.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    ats_provider: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("ats_provider.code", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    ats_board_slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    source_job_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    industry: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("industry_sector.code", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    company_dossier_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("company_dossier.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Detailed Geographic Hierarchy
    raw_location: Mapped[str] = mapped_column(
        String(500), default="Remote", nullable=False
    )
    city: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    state_province: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_province_code: Mapped[str | None] = mapped_column(
        String(50), index=True, nullable=True
    )
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(
        String(10), index=True, nullable=True
    )
    primary_region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    workplace_type: Mapped[str] = mapped_column(
        String(50), default="on_site", index=True, nullable=False
    )  # 'on_site', 'hybrid', 'remote'
    remote_scope: Mapped[str] = mapped_column(
        String(50), default="none", index=True, nullable=False
    )  # 'none', 'state_province', 'country_wide', 'worldwide_global'

    # Compensation & Content
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    ats_requirements: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Multi-Jurisdiction Visa Sponsorship Attributes
    visa_sponsorship: Mapped[str | None] = mapped_column(
        String(50), index=True, nullable=True
    )  # 'yes', 'no', 'transfer_only', 'opt_cpt_accepted', NULL
    visa_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    visa_types: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # Provenance & Deduplication
    fingerprint: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", index=True, nullable=False
    )
    data_origin: Mapped[str] = mapped_column(String(50), default="live", nullable=False)
    source_confidence: Mapped[str] = mapped_column(
        String(50), default="high", nullable=False
    )
    verification: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    extraction_version: Mapped[str] = mapped_column(
        String(50), default="v2", nullable=False
    )

    # Timestamps
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    ats_board: Mapped["ATSBoard"] = relationship(
        "ATSBoard",
        back_populates="job_listings",
    )
    company_dossier: Mapped["CompanyDossier | None"] = relationship(
        "CompanyDossier",
        back_populates="job_listings",
    )
    applications: Mapped[list["Application"]] = relationship(
        "Application",
        back_populates="job_listing",
    )
    match_caches: Mapped[list["JobMatchCache"]] = relationship(
        "JobMatchCache",
        back_populates="job_listing",
    )
