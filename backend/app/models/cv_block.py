"""CVBlock model storing chunked user career achievements and embeddings."""

import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class CVBlock(Base, UUIDMixin, TimestampMixin):
    """Stores granular career achievement blocks with pgvector embeddings."""

    __tablename__ = "cv_block"

    user_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profile.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g. experience, project, education, skill
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    # 1536-dimensional vector embedding for semantic search
    embedding = mapped_column(Vector(1536), nullable=True)

    # Relationships
    user_profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="cv_blocks",
    )
