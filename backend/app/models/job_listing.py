"""JobListing model storing raw descriptions, requirements, and metadata."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company_dossier import CompanyDossier


class JobListing(Base, UUIDMixin, TimestampMixin):
    """Stores discovered job listings, raw job descriptions, and ATS criteria."""

    __tablename__ = "job_listing"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    location: Mapped[str] = mapped_column(String(255), default="Remote", nullable=False)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    ats_requirements: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
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
