"""
Tests for persistent PostgreSQL-backed ingestion queue.
"""

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
