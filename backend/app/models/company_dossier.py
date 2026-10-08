"""
CompanyDossier model storing researched intelligence on target employers.

To ground CV tailoring and interview coaching in real-world facts rather than
hallucinations, Career-OS persists synthesized employer dossiers. This model
captures the company's verified tech stack, recent news milestones, business
model, and engineering culture notes.

Design Decisions:
  - Unique Index on ``company_name``: Prevents duplicate dossier rows when
    multiple job postings originate from the same employer.
  - JSON Fields: Tech stacks (list of strings) and recent news items (list of dicts)
    are stored as structured JSON to accommodate evolving external schemas.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job_listing import JobListing


class CompanyDossier(Base, UUIDMixin, TimestampMixin):
    """
    Stores deep intelligence on company tech stacks, news, and business models.

    Attributes:
        company_name: Unique, indexed name of the employer.
        canonical_name: Normalized name for entity resolution.
        domain: Primary web domain (e.g. "nexusai.com").
        aliases: List of alternative legal or trade names.
        industry: Primary sector (e.g. "Artificial Intelligence").
        tech_stack: JSON array of identified languages, frameworks, and databases.
        recent_news: JSON array of headlines, dates, and publication sources.
        business_model: Text description of how the company generates revenue.
        culture_notes: Text observations on engineering practices and values.
        data_origin: Origin status (live, inferred, manual, demo, legacy).
        schema_version: Extraction format version.
        field_provenance: Audit trail per field (source URLs, confidence, method).
        last_fetched_at: Timestamp of latest verification.
        next_refresh_at: Scheduled stale-while-revalidate timestamp.
        job_listings: One-to-many relationship to associated job postings.
    """

    __tablename__ = "company_dossier"

    company_name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    canonical_name: Mapped[str] = mapped_column(
        String(255), default="", index=True, nullable=False
    )
    domain: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recent_news: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    business_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    culture_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_origin: Mapped[str] = mapped_column(
        String(50), default="legacy", nullable=False
    )
    schema_version: Mapped[str] = mapped_column(
        String(50), default="v1", nullable=False
    )
    field_provenance: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_refresh_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )

    # Relationships
    job_listings: Mapped[list["JobListing"]] = relationship(
        "JobListing",
        back_populates="company_dossier",
    )
