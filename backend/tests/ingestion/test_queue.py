"""
Tests for persistent PostgreSQL-backed ingestion queue.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import IngestionTaskStatus, IngestionTaskType
from app.ingestion.queue import IngestionQueue


@pytest.mark.asyncio
async def test_queue_enqueue_dequeue_complete(db_session: AsyncSession) -> None:
    queue = IngestionQueue(db_session)

    # Enqueue task
    task = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key="sync:greenhouse:stripe",
        payload={"provider": "greenhouse", "slug": "stripe"},
        priority=8,
    )
    assert task is not None
    assert task.status == IngestionTaskStatus.PENDING

    # Dequeue task
    dequeued = await queue.dequeue_next_task()
    assert dequeued is not None
    assert dequeued.dedupe_key == "sync:greenhouse:stripe"
    assert dequeued.status == IngestionTaskStatus.PROCESSING

    # Complete task
    await queue.complete_task(dequeued.id)
    assert dequeued.status == IngestionTaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_queue_deduplication(db_session: AsyncSession) -> None:
    queue = IngestionQueue(db_session)
    dedupe_key = "sync:lever:postman"

    task1 = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key=dedupe_key,
        payload={"slug": "postman"},
    )
    assert task1 is not None

    # Enqueue duplicate while pending should return existing
    task2 = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key=dedupe_key,
        payload={"slug": "postman"},
    )
    assert task2 is not None
    assert task1.id == task2.id


@pytest.mark.asyncio
async def test_queue_retry_and_backoff(db_session: AsyncSession) -> None:
    queue = IngestionQueue(db_session)
    task = await queue.enqueue_task(
        task_type=IngestionTaskType.INGEST_URL,
        dedupe_key="url:test-job",
        payload={"url": "https://example.com/job"},
    )
    assert task is not None

    # First failure -> retry with backoff
    await queue.fail_task(task.id, "Connection refused")
    assert task.retry_count == 1
    assert task.status == IngestionTaskStatus.PENDING

    # Fail remaining retries -> marks as FAILED
    await queue.fail_task(task.id, "Connection refused 2")
    await queue.fail_task(task.id, "Connection refused 3")
    assert task.retry_count == 3
    assert task.status == IngestionTaskStatus.FAILED


@pytest.mark.asyncio
async def test_queue_reclaims_expired_processing_task(
    db_session: AsyncSession,
) -> None:
    """Verify an orphaned processing task whose lease expired gets dequeued with incremented retry count."""
    queue = IngestionQueue(db_session)
    task = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key="sync:greenhouse:expired_test",
        payload={"provider": "greenhouse", "slug": "expired_test"},
    )
    assert task is not None

    dequeued = await queue.dequeue_next_task(lock_duration_seconds=300)
    assert dequeued is not None
    assert dequeued.status == IngestionTaskStatus.PROCESSING
    assert dequeued.retry_count == 0

    # Simulate worker crash: lease expired 1 minute ago
    dequeued.locked_until = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.flush()

    # Reclaiming worker dequeues the expired task
    reclaimed = await queue.dequeue_next_task(lock_duration_seconds=300)
    assert reclaimed is not None
    assert reclaimed.id == task.id
    assert reclaimed.status == IngestionTaskStatus.PROCESSING
    assert reclaimed.retry_count == 1
    assert reclaimed.locked_until > datetime.now(UTC)


@pytest.mark.asyncio
async def test_queue_skips_active_lease_processing_task(
    db_session: AsyncSession,
) -> None:
    """Verify an actively locked processing task with unexpired lease is not dequeued."""
    queue = IngestionQueue(db_session)
    task = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key="sync:active:lease",
        payload={"provider": "lever", "slug": "active"},
    )
    assert task is not None

    dequeued = await queue.dequeue_next_task(lock_duration_seconds=600)
    assert dequeued is not None

    # Next dequeue attempt should return None since task is actively locked
    no_task = await queue.dequeue_next_task()
    assert no_task is None


@pytest.mark.asyncio
async def test_queue_enqueue_reclaims_expired_task(
    db_session: AsyncSession,
) -> None:
    """Verify enqueue_task resets an abandoned processing task to pending when lease expired."""
    queue = IngestionQueue(db_session)
    dedupe = "sync:enqueue:reclaim"
    task = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key=dedupe,
        payload={"stage": 1},
    )
    assert task is not None

    dequeued = await queue.dequeue_next_task()
    assert dequeued is not None

    # Expire the lease
    dequeued.locked_until = datetime.now(UTC) - timedelta(seconds=30)
    await db_session.flush()

    # Enqueue should reclaim and reset to pending
    reclaimed = await queue.enqueue_task(
        task_type=IngestionTaskType.SYNC_BOARD,
        dedupe_key=dedupe,
        payload={"stage": 2},
    )
    assert reclaimed is not None
    assert reclaimed.id == task.id
    assert reclaimed.status == IngestionTaskStatus.PENDING
    assert reclaimed.locked_until is None
    assert reclaimed.payload["stage"] == 2
