"""
Persistent job queue implementation backed by PostgreSQL.

Uses SELECT FOR UPDATE SKIP LOCKED for atomic, lock-free concurrency across
multiple worker processes.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import IngestionTaskStatus, IngestionTaskType
from app.models.ingestion import IngestionTask

logger = logging.getLogger("career_os.ingestion.queue")


class IngestionQueue:
    """
    Queue manager for asynchronous board synchronizations, URL ingestions,
    and background enrichment tasks.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue_task(
        self,
        task_type: IngestionTaskType | str,
        dedupe_key: str,
        payload: dict[str, Any],
        priority: int = 5,
        scheduled_for: datetime | None = None,
    ) -> IngestionTask | None:
        """
        Enqueue a new ingestion task. If dedupe_key already exists in pending
        or processing state, skips creation to prevent duplicate runs.
        """
        stmt = select(IngestionTask).where(IngestionTask.dedupe_key == dedupe_key)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        if existing:
            if existing.status in (
                IngestionTaskStatus.PENDING,
                IngestionTaskStatus.PROCESSING,
            ):
                logger.info(
                    "Task dedupe_key '%s' is already %s; skipping.",
                    dedupe_key,
                    existing.status,
                )
                return existing

        task = IngestionTask(
            task_type=str(task_type),
            dedupe_key=dedupe_key,
            payload=payload,
            priority=priority,
            status=IngestionTaskStatus.PENDING,
            scheduled_for=scheduled_for or datetime.now(UTC),
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def dequeue_next_task(
        self, lock_duration_seconds: int = 600
    ) -> IngestionTask | None:
        """
        Fetch the highest-priority pending task and lock it with SKIP LOCKED.
        """
        now = datetime.now(UTC)
        stmt = (
            select(IngestionTask)
            .where(
                IngestionTask.status == IngestionTaskStatus.PENDING,
                IngestionTask.scheduled_for <= now,
            )
            .order_by(IngestionTask.priority.desc(), IngestionTask.scheduled_for.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            task.status = IngestionTaskStatus.PROCESSING
            task.locked_until = now + timedelta(seconds=lock_duration_seconds)
            await self.session.flush()

        return task

    async def complete_task(self, task_id: Any) -> None:
        """Mark a task as completed."""
        stmt = (
            select(IngestionTask).where(IngestionTask.id == task_id).with_for_update()
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()
        if task:
            task.status = IngestionTaskStatus.COMPLETED
            task.locked_until = None
            await self.session.flush()

    async def fail_task(self, task_id: Any, error_message: str) -> None:
        """Record failure, increment retry count, or mark as permanently failed."""
        stmt = (
            select(IngestionTask).where(IngestionTask.id == task_id).with_for_update()
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()
        if task:
            task.retry_count += 1
            task.error_message = error_message
            if task.retry_count >= task.max_retries:
                task.status = IngestionTaskStatus.FAILED
            else:
                task.status = IngestionTaskStatus.PENDING
                # Exponential backoff retry
                task.scheduled_for = datetime.now(UTC) + timedelta(
                    seconds=30 * (2**task.retry_count)
                )
            task.locked_until = None
            await self.session.flush()
