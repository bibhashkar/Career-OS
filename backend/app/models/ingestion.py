"""
SQLAlchemy ORM models for the ingestion subsystem.

Tables:
- ats_board: Registry of tracked ATS company career portals.
- ingestion_run: Metrics and telemetry for synchronization batches.
- provider_usage: Persistent atomic ledger tracking quota consumption.
- provider_state: Circuit-breaker status and cooldown records.
- ingestion_task: Asynchronous queue table processed via FOR UPDATE SKIP LOCKED.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ATSBoard(Base, UUIDMixin, TimestampMixin):
    """
    Registry of tracked ATS career boards (e.g. greenhouse/stripe, lever/postman).
    """

    __tablename__ = "ats_board"
    __table_args__ = (
        UniqueConstraint("provider", "slug", name="uq_ats_board_provider_slug"),
    )

    provider: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1, 2, or 3
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1 to 10
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    discovered_via: Mapped[str] = mapped_column(
        String(50), default="seed", nullable=False
    )  # seed, probe, snowball, user, dork


class IngestionRun(Base, UUIDMixin, TimestampMixin):
    """
    Telemetry and performance metrics for an ingestion sync run.
    """

    __tablename__ = "ingestion_run"

    source: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    board_slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # success, partial, failed
    fetched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    closed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ProviderUsage(Base, UUIDMixin, TimestampMixin):
    """
    Persistent atomic rate-limit and daily quota tracking per provider.
    """

    __tablename__ = "provider_usage"
    __table_args__ = (
        UniqueConstraint("provider", "period_key", name="uq_provider_usage_period"),
    )

    provider: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    period_key: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # e.g., '2026-10-08' or '2026-10-08-14:55'
    call_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_calls: Mapped[int] = mapped_column(Integer, nullable=False)


class ProviderState(Base, UUIDMixin, TimestampMixin):
    """
    Circuit-breaker state tracking for external providers and scraping adapters.
    """

    __tablename__ = "provider_state"

    provider: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    is_circuit_open: Mapped[bool] = mapped_column(default=False, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cooldown_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionTask(Base, UUIDMixin, TimestampMixin):
    """
    Persistent ingestion queue table, locked via SELECT FOR UPDATE SKIP LOCKED.
    """

    __tablename__ = "ingestion_task"

    task_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True, nullable=False
    )  # pending, processing, completed, failed
    priority: Mapped[int] = mapped_column(
        Integer, default=5, index=True, nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True,
        nullable=False,
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
