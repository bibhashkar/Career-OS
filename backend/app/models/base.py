"""
Base SQLAlchemy declarative model and common audit mixins.

This module provides the foundation for all relational domain models in Career-OS:
  - ``Base``: Central DeclarativeBase instance for schema registration.
  - ``TimestampMixin``: Consistent audit timestamps across all entities.
  - ``UUIDMixin``: Standard UUIDv4 primary keys for distributed identification.

Architectural Design Principles:
  1. Timezone-Aware UTC: All timestamps are stored as ``TIMESTAMP WITH TIME ZONE``
     in PostgreSQL, defaulting to ``datetime.now(UTC)``. This eliminates daylight
     savings bugs and ambiguity across geographically distributed deployments.
  2. UUID Primary Keys: Using UUIDs instead of auto-incrementing integers prevents
     sequential ID enumeration attacks and allows client or worker processes to
     generate entity IDs prior to database persistence.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy relational models."""

    pass


class TimestampMixin:
    """
    Reusable mixin providing created_at and updated_at audit timestamps.

    All timestamps are timezone-aware UTC to ensure consistency across
    different deployment regions and daylight savings transitions.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class UUIDMixin:
    """
    Reusable mixin providing standard UUIDv4 primary keys.

    Prevents enumeration attacks and enables distributed ID generation
    before database insertion.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
