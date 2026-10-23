"""
Background ingestion worker process entrypoint.

Polls the persistent PostgreSQL queue using SELECT FOR UPDATE SKIP LOCKED
and executes board synchronization, URL ingestion, and intelligence updates.
"""

import asyncio
import logging
import signal
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.core.database import get_session_context
from app.core.logging import set_correlation_id
from app.core.tracing import flush_tracing, setup_tracing
from app.ingestion.adapters.ats import (
    AshbyAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    SmartRecruitersAdapter,
    WorkableAdapter,
)
from app.ingestion.company_intel_provider import ProvenanceCompanyIntelProvider
from app.ingestion.discovery import BoardDiscoveryEngine
from app.ingestion.extractor import HybridRequirementsExtractor
from app.ingestion.ledger import CircuitBreaker, PersistentBudgetLedger
from app.ingestion.models import (
    ATSProvider,
    DataOrigin,
    IngestionTaskType,
    SourceConfidence,
)
from app.ingestion.queue import IngestionQueue
from app.ingestion.security import parse_ats_url
from app.ingestion.service import (
    BoardSyncService,
    compute_content_hash,
    compute_dedupe_fingerprint,
)
from app.ingestion.verification import JobVerificationService
from app.models.job_listing import JobListing

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

            set_correlation_id(str(task.id))
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

            service = BoardSyncService(session)
            run = await service.sync_board(provider, slug)
            if run.status == "failed":
                await breaker.record_failure(provider, run.error_message)
                raise RuntimeError(f"Board sync failed: {run.error_message}")
            else:
                await breaker.record_success(provider)
        elif task_type == IngestionTaskType.INGEST_URL:
            url = payload.get("url", "")
            if not url:
                raise ValueError("INGEST_URL payload missing url")

            parsed = parse_ats_url(url)
            if not parsed:
                raise ValueError(f"URL is not a recognized ATS posting URL: {url}")
            provider, slug, job_id = parsed
            if not job_id:
                raise ValueError(f"URL is missing job_id: {url}")

            adapter_map = {
                ATSProvider.GREENHOUSE: GreenhouseAdapter(),
                ATSProvider.LEVER: LeverAdapter(),
                ATSProvider.ASHBY: AshbyAdapter(),
                ATSProvider.WORKABLE: WorkableAdapter(),
                ATSProvider.SMARTRECRUITERS: SmartRecruitersAdapter(),
            }
            adapter = adapter_map.get(provider)
            if not adapter:
                raise ValueError(f"No adapter found for ATS provider: {provider}")

            job_dto = await adapter.fetch_job_detail(slug, job_id)
            if not job_dto:
                raise RuntimeError(f"Could not fetch job details for {slug}:{job_id}")

            # Register board if not already present
            discovery = BoardDiscoveryEngine(session)
            board = await discovery.register_board_if_not_exists(
                provider=provider,
                slug=slug,
                company_name=job_dto.company_name,
                discovered_via="url_ingest",
            )
            if not board:
                sync_service = BoardSyncService(session)
                board = await sync_service.get_or_create_board(provider, slug)

            # Extract requirements
            extractor = HybridRequirementsExtractor()
            reqs = await extractor.extract_requirements(
                title=job_dto.title,
                raw_description=job_dto.raw_description,
                company_name=job_dto.company_name,
            )

            # Upsert into JobListing
            stmt = select(JobListing).where(
                JobListing.ats_provider == job_dto.ats_provider,
                JobListing.ats_board_slug == job_dto.ats_board_slug,
                JobListing.source_job_id == job_dto.source_job_id,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            now = datetime.now(UTC)
            fingerprint = compute_dedupe_fingerprint(
                job_dto.company_name, job_dto.title, job_dto.raw_location
            )
            content_hash = compute_content_hash(job_dto.raw_description)

            modality = (
                job_dto.workplace_type.value
                if hasattr(job_dto.workplace_type, "value")
                else str(job_dto.workplace_type)
            )
            scope = (
                job_dto.remote_scope.value
                if hasattr(job_dto.remote_scope, "value")
                else str(job_dto.remote_scope)
            )
            job_industry = board.industry or job_dto.industry or "enterprise_saas"

            if existing is None:
                new_job = JobListing(
                    ats_board_id=board.id,
                    ats_provider=job_dto.ats_provider,
                    ats_board_slug=job_dto.ats_board_slug,
                    source_job_id=job_dto.source_job_id,
                    industry=job_industry,
                    company_dossier_id=board.company_dossier_id,
                    title=job_dto.title,
                    company_name=board.company_name or job_dto.company_name,
                    apply_url=job_dto.apply_url,
                    url=job_dto.apply_url,
                    raw_location=job_dto.raw_location,
                    city=job_dto.city,
                    state_province=job_dto.state_province,
                    state_province_code=job_dto.state_province_code,
                    country=job_dto.country,
                    country_code=job_dto.country_code,
                    primary_region=job_dto.primary_region or board.primary_region,
                    workplace_type=modality,
                    remote_scope=scope,
                    salary_range=job_dto.salary_range,
                    raw_description=job_dto.raw_description,
                    posted_at=job_dto.posted_at,
                    first_seen_at=now,
                    last_seen_at=now,
                    last_fetched_at=now,
                    fingerprint=fingerprint,
                    content_hash=content_hash,
                    status="active",
                    data_origin=str(DataOrigin.LIVE),
                    source_confidence=str(SourceConfidence.HIGH),
                    visa_sponsorship=job_dto.visa_sponsorship
                    or str(reqs.visa_sponsorship),
                    visa_notes=job_dto.visa_notes,
                    visa_types=job_dto.visa_types,
                    industry_vertical=reqs.industry_vertical,
                    domain_strictness=reqs.domain_strictness,
                    ats_requirements=reqs.model_dump(),
                    verification={},
                )
                session.add(new_job)
            else:
                existing.last_seen_at = now
                existing.last_fetched_at = now
                existing.raw_description = job_dto.raw_description
                existing.industry_vertical = reqs.industry_vertical
                existing.domain_strictness = reqs.domain_strictness
                existing.ats_requirements = reqs.model_dump()
                if job_dto.visa_sponsorship:
                    existing.visa_sponsorship = job_dto.visa_sponsorship
                existing.workplace_type = modality
                existing.remote_scope = scope
                existing.raw_location = job_dto.raw_location
                if job_dto.city:
                    existing.city = job_dto.city
                if job_dto.state_province_code:
                    existing.state_province_code = job_dto.state_province_code
                if job_dto.country_code:
                    existing.country_code = job_dto.country_code
                existing.status = "active"

            await session.flush()
            logger.info("Successfully ingested job from URL: %s", url)

        elif task_type == IngestionTaskType.REFRESH_COMPANY:
            company_name = payload.get("company_name", "")
            if not company_name:
                raise ValueError("REFRESH_COMPANY payload missing company_name")

            intel_provider = ProvenanceCompanyIntelProvider(session)
            await intel_provider.fetch_company_intel(
                company_name=company_name,
                domain=payload.get("domain"),
            )
            logger.info("Successfully refreshed company intel for: %s", company_name)

        elif task_type == IngestionTaskType.CROSS_CHECK_JOB:
            job_id_str = payload.get("job_id", "")
            if not job_id_str:
                raise ValueError("CROSS_CHECK_JOB payload missing job_id")

            verification_service = JobVerificationService(session)
            await verification_service.verify_job(uuid.UUID(job_id_str), force=True)
            logger.info("Successfully cross-checked job: %s", job_id_str)

        else:
            logger.warning("Unhandled task type '%s'", task_type)


def main() -> None:
    """CLI entrypoint for running the worker."""
    setup_tracing()
    worker = IngestionWorker()

    def handle_signal(sig: int, frame: Any) -> None:
        worker.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        pass
    finally:
        flush_tracing()


if __name__ == "__main__":
    main()
