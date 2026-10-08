"""
JobListing model storing raw descriptions, requirements, and metadata.

This table records job postings discovered by the Hunter agent or manually
imported by the user. It stores raw job descriptions alongside parsed ATS
requirements (required skills, preferred skills, min experience, visa policy).

Relational Foreign Key Safety:
  - ``company_dossier_id`` is nullable, allowing job listings to be captured
    immediately upon discovery before the deep-dive research conducted by
    the Intel agent completes.
  - Foreign key uses ``ondelete="RESTRICT"`` per project architectural rules,
    preventing employer dossiers from being dropped while active job listings
    still reference them.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company_dossier import CompanyDossier


class JobListing(Base, UUIDMixin, TimestampMixin):
    """
    Stores discovered job listings, raw job descriptions, and ATS criteria.

    Attributes:
        title: Position title (e.g. 'Senior AI Systems Engineer').
        company_name: Hiring organization name, indexed for fast lookup.
        url: External application or posting URL.
        location: Geographic location or 'Remote'.
        salary_range: Compensation range string if disclosed.
        raw_description: Full text of the posting for keyword extraction.
        ats_requirements: JSON dictionary of parsed skills and visa policies.
        company_dossier_id: Optional foreign key to associated CompanyDossier.
        company_dossier: Relationship to the employer's researched intelligence.
    """

    __tablename__ = "job_listing"
    __table_args__ = (
        UniqueConstraint(
            "source", "source_job_id", name="uq_job_listing_source_job_id"
        ),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    location: Mapped[str] = mapped_column(String(255), default="Remote", nullable=False)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    ats_requirements: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Ingestion pipeline provenance & deduplication fields
    source: Mapped[str] = mapped_column(
        String(100), default="legacy", index=True, nullable=False
    )
    source_job_id: Mapped[str] = mapped_column(
        String(255), default="", index=True, nullable=False
    )
    apply_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", index=True, nullable=False
    )
    data_origin: Mapped[str] = mapped_column(
        String(50), default="legacy", nullable=False
    )
    source_confidence: Mapped[str] = mapped_column(
        String(50), default="high", nullable=False
    )
    visa_sponsorship: Mapped[str] = mapped_column(
        String(50), default="unknown", nullable=False
    )
    remote_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extraction_version: Mapped[str] = mapped_column(
        String(50), default="v1", nullable=False
    )
    verification: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

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

    # Foreign Key to CompanyDossier (ON DELETE RESTRICT per rules)
    company_dossier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("company_dossier.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Relationships
    company_dossier: Mapped["CompanyDossier | None"] = relationship(
        "CompanyDossier",
        back_populates="job_listings",
    )
