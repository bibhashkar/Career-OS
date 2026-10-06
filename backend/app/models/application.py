"""
Application model storing candidate job application tracker statuses.

Tracks the progress of a candidate's applications across canonical stages:
  - 'saved': Saved listing for later review.
  - 'applied': Submitted application.
  - 'interviewing': Active interview loop (mock or live).
  - 'offered': Job offer extended.
  - 'rejected': Process terminated.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job_listing import JobListing
    from app.models.user_profile import UserProfile


class Application(Base, UUIDMixin, TimestampMixin):
    """
    Candidate application tracking record.

    Attributes:
        user_profile_id: Foreign key to candidate UserProfile.
        job_listing_id: Foreign key to target JobListing.
        status: Application stage ('saved', 'applied', etc.).
        notes: Candidate personal preparation notes or interview logs.
        custom_metadata: JSON store for expectations, recruiters, dates.
    """

    __tablename__ = "application"

    user_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profile.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    job_listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_listing.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="saved", nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    user_profile: Mapped["UserProfile"] = relationship("UserProfile")
    job_listing: Mapped["JobListing"] = relationship("JobListing")
