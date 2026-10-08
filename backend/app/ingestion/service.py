"""
Board synchronization service and deduplication engine.

Calculates cross-source deduplication fingerprints:
  fingerprint = hash(normalized company, normalized title, normalized location region)
and performs atomic upserts, tracking first_seen_at, last_seen_at, and soft-closing
jobs absent from consecutive board syncs.
"""

import hashlib
import logging
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.adapters.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter
from app.ingestion.models import (
    ATSProvider,
    DiscoveredJobDTO,
    ListingStatus,
)
from app.ingestion.ports.provider import ATSAdapterPort
from app.models.ingestion import ATSBoard, IngestionRun
from app.models.job_listing import JobListing

logger = logging.getLogger("career_os.ingestion.service")


def compute_dedupe_fingerprint(company: str, title: str, location: str) -> str:
    """
    Compute cross-source dedupe fingerprint:
    hash(normalized company, normalized title, normalized location region).
    """
    norm_company = re.sub(r"[^a-z0-9]", "", company.lower())
    norm_title = re.sub(r"[^a-z0-9]", "", title.lower())
    norm_loc = re.sub(r"[^a-z0-9]", "", location.lower())
    raw = f"{norm_company}:{norm_title}:{norm_loc}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def compute_content_hash(description: str) -> str:
    """Compute sha256 hash of job description text for change tracking."""
    return hashlib.sha256(description.encode("utf-8")).hexdigest()[:32]


class BoardSyncService:
    """
    Synchronizes jobs from an ATS board into the local job_listing store.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._adapters: dict[ATSProvider, ATSAdapterPort] = {
            ATSProvider.GREENHOUSE: GreenhouseAdapter(),
            ATSProvider.LEVER: LeverAdapter(),
            ATSProvider.ASHBY: AshbyAdapter(),
        }

    def register_adapter(self, provider: ATSProvider, adapter: ATSAdapterPort) -> None:
        """Register custom or mocked ATS adapter."""
        self._adapters[provider] = adapter

    async def sync_board(self, provider_str: str, slug: str) -> IngestionRun:
        """
        Execute full board sync:
        1. Fetch open jobs via provider adapter.
        2. Upsert into job_listing table.
        3. Detect missing jobs and soft-close them.
        4. Log metrics to ingestion_run table.
        """
        start_time = datetime.now(UTC)
        provider = ATSProvider(provider_str.lower())
        adapter = self._adapters.get(provider)

        if not adapter:
            raise ValueError(f"No adapter registered for ATS provider '{provider_str}'")

        run = IngestionRun(
            source=f"{provider}:{slug}",
            board_slug=slug,
            status="running",
            fetched_count=0,
            new_count=0,
            updated_count=0,
            closed_count=0,
            rejected_count=0,
            duration_ms=0,
        )
        self.session.add(run)
        await self.session.flush()

        try:
            discovered_jobs = await adapter.fetch_board_jobs(slug)
            run.fetched_count = len(discovered_jobs)

            source_prefix = f"{provider}:{slug}"
            current_source_ids = {j.source_job_id for j in discovered_jobs}

            # Upsert discovered jobs
            for dto in discovered_jobs:
                is_new = await self._upsert_job(dto)
                if is_new:
                    run.new_count += 1
                else:
                    run.updated_count += 1

            # Detect closed jobs:
            # currently active jobs for this source absent from response
            stmt = select(JobListing).where(
                JobListing.source == source_prefix,
                JobListing.status == ListingStatus.ACTIVE,
            )
            existing_active = (await self.session.execute(stmt)).scalars().all()

            for active_job in existing_active:
                if active_job.source_job_id not in current_source_ids:
                    active_job.status = ListingStatus.CLOSED
                    active_job.last_seen_at = datetime.now(UTC)
                    run.closed_count += 1

            # Update ATSBoard metadata if registered
            board_stmt = select(ATSBoard).where(
                ATSBoard.provider == str(provider),
                ATSBoard.slug == slug,
            )
            board = (await self.session.execute(board_stmt)).scalar_one_or_none()
            if board:
                board.last_synced_at = datetime.now(UTC)
                board.consecutive_failures = 0

            run.status = "success"

        except Exception as e:
            logger.error(
                "Board sync failed for %s:%s: %s", provider, slug, e, exc_info=True
            )
            run.status = "failed"
            run.error_message = str(e)
            # Increment board consecutive failures if registered
            board_stmt = select(ATSBoard).where(
                ATSBoard.provider == str(provider),
                ATSBoard.slug == slug,
            )
            board = (await self.session.execute(board_stmt)).scalar_one_or_none()
            if board:
                board.consecutive_failures += 1

        end_time = datetime.now(UTC)
        run.duration_ms = int((end_time - start_time).total_seconds() * 1000)
        await self.session.flush()
        return run

    async def _upsert_job(self, dto: DiscoveredJobDTO) -> bool:
        """
        Upsert a discovered job listing.
        Returns True if newly created, False if updated.
        """
        stmt = select(JobListing).where(
            JobListing.source == dto.source,
            JobListing.source_job_id == dto.source_job_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        now = datetime.now(UTC)
        fingerprint = compute_dedupe_fingerprint(
            dto.company_name, dto.title, dto.location
        )
        content_hash = compute_content_hash(dto.raw_description)

        if existing is None:
            new_job = JobListing(
                source=dto.source,
                source_job_id=dto.source_job_id,
                title=dto.title,
                company_name=dto.company_name,
                apply_url=dto.apply_url,
                url=dto.apply_url,
                location=dto.location,
                salary_range=dto.salary_range,
                raw_description=dto.raw_description,
                remote_type=dto.remote_type,
                posted_at=dto.posted_at,
                first_seen_at=now,
                last_seen_at=now,
                last_fetched_at=now,
                fingerprint=fingerprint,
                content_hash=content_hash,
                status=ListingStatus.ACTIVE,
                data_origin=str(dto.data_origin),
                source_confidence=str(dto.source_confidence),
                ats_requirements={},
                verification={},
            )
            self.session.add(new_job)
            return True

        # Existing job: update timestamps, text if modified, and reactivate
        existing.last_seen_at = now
        existing.last_fetched_at = now
        existing.apply_url = dto.apply_url
        existing.status = ListingStatus.ACTIVE

        if existing.content_hash != content_hash:
            existing.raw_description = dto.raw_description
            existing.content_hash = content_hash
            existing.title = dto.title
            existing.location = dto.location

        return False
