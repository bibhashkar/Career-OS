"""
Tests for BoardSyncService lifecycle, fingerprinting, and closed job detection.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import (
    ATSProvider,
    DiscoveredJobDTO,
    ListingStatus,
)
from app.ingestion.ports.provider import ATSAdapterPort
from app.ingestion.service import BoardSyncService, compute_dedupe_fingerprint
from app.models.job_listing import JobListing


class FakeGreenhouseAdapter(ATSAdapterPort):
    """Hermetic test adapter returning controllable job listings."""

    def __init__(self, jobs: list[DiscoveredJobDTO]) -> None:
        self.jobs = jobs

    @property
    def provider(self) -> ATSProvider:
        return ATSProvider.GREENHOUSE

    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        return self.jobs

    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        for j in self.jobs:
            if j.source_job_id == job_id:
                return j
        return None


@pytest.mark.asyncio
async def test_fingerprint_generation_is_stable_and_region_sensitive() -> None:
    fp1 = compute_dedupe_fingerprint(
        "Stripe", "Senior Backend Engineer", "San Francisco, CA"
    )
    fp2 = compute_dedupe_fingerprint(
        "stripe", "senior backend engineer", "san francisco, ca"
    )
    # Same company, title, location should generate identical fingerprint
    assert fp1 == fp2

    # Same title and company but different location region
    # must generate DIFFERENT fingerprint
    fp_london = compute_dedupe_fingerprint(
        "Stripe", "Senior Backend Engineer", "London, UK"
    )
    assert fp1 != fp_london


@pytest.mark.asyncio
async def test_board_sync_lifecycle_and_closed_job_detection(
    db_session: AsyncSession,
) -> None:
    job_101 = DiscoveredJobDTO(
        source="greenhouse:stripe",
        source_job_id="101",
        title="Senior Backend Engineer",
        company_name="Stripe",
        apply_url="https://boards.greenhouse.io/stripe/jobs/101",
        location="San Francisco, CA",
        raw_description="Python distributed systems engineer.",
    )
    job_102 = DiscoveredJobDTO(
        source="greenhouse:stripe",
        source_job_id="102",
        title="AI Engineer",
        company_name="Stripe",
        apply_url="https://boards.greenhouse.io/stripe/jobs/102",
        location="Remote",
        raw_description="ML agent workflows.",
    )

    fake_adapter = FakeGreenhouseAdapter([job_101, job_102])
    service = BoardSyncService(db_session)
    service.register_adapter(ATSProvider.GREENHOUSE, fake_adapter)

    # Initial sync: 2 new jobs
    run1 = await service.sync_board("greenhouse", "stripe")
    assert run1.status == "success"
    assert run1.fetched_count == 2
    assert run1.new_count == 2
    assert run1.closed_count == 0

    # Verify both jobs are in database and ACTIVE
    stmt = select(JobListing).where(JobListing.source == "greenhouse:stripe")
    listings = (await db_session.execute(stmt)).scalars().all()
    assert len(listings) == 2
    for item in listings:
        assert item.status == ListingStatus.ACTIVE

    # Second sync: job_101 is filled/closed, only job_102 is present
    fake_adapter.jobs = [job_102]
    run2 = await service.sync_board("greenhouse", "stripe")
    assert run2.status == "success"
    assert run2.fetched_count == 1
    assert run2.new_count == 0
    assert run2.updated_count == 1
    assert run2.closed_count == 1

    # Verify job_101 is now marked CLOSED and job_102 remains ACTIVE
    stmt_101 = select(JobListing).where(
        JobListing.source == "greenhouse:stripe",
        JobListing.source_job_id == "101",
    )
    db_job_101 = (await db_session.execute(stmt_101)).scalar_one()
    assert db_job_101.status == ListingStatus.CLOSED

    stmt_102 = select(JobListing).where(
        JobListing.source == "greenhouse:stripe",
        JobListing.source_job_id == "102",
    )
    db_job_102 = (await db_session.execute(stmt_102)).scalar_one()
    assert db_job_102.status == ListingStatus.ACTIVE
