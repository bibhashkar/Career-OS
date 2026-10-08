"""
Background ingestion worker process entrypoint.

Polls the persistent PostgreSQL queue using SELECT FOR UPDATE SKIP LOCKED
and executes board synchronization, URL ingestion, and intelligence updates.
"""

import asyncio
import logging
import signal
from typing import Any

from app.core.database import get_session_context
from app.ingestion.ledger import CircuitBreaker, PersistentBudgetLedger
from app.ingestion.models import IngestionTaskType
from app.ingestion.queue import IngestionQueue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("career_os.ingestion.worker")


class IngestionWorker:
    """
    Autonomous ingestion runner executing tasks from the ingestion_task queue.
    """

    def __init__(self, poll_interval_seconds: float = 2.0) -> None:
        self.poll_interval = poll_interval_seconds
        self.running = True

    def stop(self) -> None:
        """Signal worker to stop gracefully."""
        logger.info("Stopping ingestion worker...")
        self.running = False

    async def run(self) -> None:
        """Main event loop for the worker daemon."""
        logger.info("Ingestion worker daemon started.")

        while self.running:
            try:
                processed = await self._process_one_task()
                if not processed:
                    await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Unexpected error in worker loop: %s", e, exc_info=True)
                await asyncio.sleep(self.poll_interval)

        logger.info("Ingestion worker daemon stopped.")

    async def _process_one_task(self) -> bool:
        """Fetch and execute a single task from the database queue."""
        async with get_session_context() as session:
            queue = IngestionQueue(session)
            task = await queue.dequeue_next_task()

            if not task:
                return False

            logger.info(
                "Dequeued task %s (type=%s, dedupe_key=%s)",
                task.id,
                task.task_type,
                task.dedupe_key,
            )

            ledger = PersistentBudgetLedger(session)
            breaker = CircuitBreaker(session)

            try:
                await self._execute_task(
                    session, task.task_type, task.payload, ledger, breaker
                )
                await queue.complete_task(task.id)
                logger.info("Completed task %s", task.id)
            except Exception as e:
                logger.warning("Task %s failed: %s", task.id, e)
                await queue.fail_task(task.id, str(e))

            return True

    async def _execute_task(
        self,
        session: Any,
        task_type: str,
        payload: dict[str, Any],
        ledger: PersistentBudgetLedger,
        breaker: CircuitBreaker,
    ) -> None:
        """Route task to appropriate handler."""
        if task_type == IngestionTaskType.SYNC_BOARD:
            provider = payload.get("provider", "")
            slug = payload.get("slug", "")
            if not provider or not slug:
                raise ValueError("SYNC_BOARD payload missing provider or slug")

            if not await breaker.is_available(provider):
                raise RuntimeError(
                    f"Circuit breaker is active for provider '{provider}'"
                )

            from app.ingestion.service import BoardSyncService

            service = BoardSyncService(session)
            run = await service.sync_board(provider, slug)
            if run.status == "failed":
                await breaker.record_failure(provider, run.error_message)
                raise RuntimeError(f"Board sync failed: {run.error_message}")
            else:
                await breaker.record_success(provider)
        elif task_type == IngestionTaskType.INGEST_URL:
            logger.info("URL ingestion handler for payload: %s", payload)
        elif task_type == IngestionTaskType.REFRESH_COMPANY:
            logger.info("Company refresh handler for payload: %s", payload)
        else:
            logger.warning("Unhandled task type '%s'", task_type)


def main() -> None:
    """CLI entrypoint for running the worker."""
    worker = IngestionWorker()

    def handle_signal(sig: int, frame: Any) -> None:
        worker.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
