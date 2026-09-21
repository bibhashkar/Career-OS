"""CompanyDossier model storing researched intelligence on target employers."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job_listing import JobListing


class CompanyDossier(Base, UUIDMixin, TimestampMixin):
    """Stores deep intelligence on company tech stacks, news, and business models."""

    __tablename__ = "company_dossier"

    company_name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recent_news: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    business_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    culture_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    job_listings: Mapped[list["JobListing"]] = relationship(
        "JobListing",
        back_populates="company_dossier",
    )
