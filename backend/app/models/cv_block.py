"""
CVBlock model storing chunked user career achievements and embeddings.

Career-OS does not treat a resume as an immutable text document. Instead, a
candidate's career history is decomposed into modular, semantic "blocks"
representing distinct projects, leadership achievements, technical roles, or
publications.

Semantic Retrieval Architecture:
  - Each block stores a 1536-dimensional vector embedding (matching OpenAI
    text-embedding-3-small or Ada-002 dimensions) using the PostgreSQL
    ``pgvector`` extension.
  - When tailoring a CV for a target job, the system retrieves only the blocks
    whose embeddings most closely match the job requirements, dynamically
    assembling a bespoke resume.

Foreign Key Safety:
  - ``user_profile_id`` uses ``ondelete="RESTRICT"`` per project rules,
    preventing cascade deletion of career blocks unless the user profile is
    explicitly archived or purged.
"""

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
    """
    Stores granular career achievement blocks with pgvector embeddings.

    Attributes:
        user_profile_id: Foreign key to owning user profile (ON DELETE RESTRICT).
        category: Taxonomy type (e.g. 'experience', 'project', 'education').
        title: Position or project title.
        organization: Sponsoring company, institution, or open-source org.
        content: Narrative description of the achievement with quantified impact.
        metrics: Quantified business results (e.g. {'latency': '-40%', 'scale': '10M'}).
        skills: List of technical competencies demonstrated in this achievement.
        embedding: 1536-dimensional vector embedding for pgvector cosine search.
        user_profile: Relationship back to the parent UserProfile entity.
    """

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

    # 1536-dimensional vector embedding for pgvector semantic search
    embedding = mapped_column(Vector(1536), nullable=True)

    # Relationships
    user_profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="cv_blocks",
    )
