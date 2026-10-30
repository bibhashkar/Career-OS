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
    WorkplaceType,
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
        ats_provider="greenhouse",
        ats_board_slug="stripe",
        source_job_id="101",
        title="Senior Backend Engineer",
        company_name="Stripe",
        apply_url="https://boards.greenhouse.io/stripe/jobs/101",
        raw_location="San Francisco, CA",
        city="San Francisco",
        state_province_code="CA",
        country_code="US",
        raw_description="Python distributed systems engineer.",
    )
    job_102 = DiscoveredJobDTO(
        ats_provider="greenhouse",
        ats_board_slug="stripe",
        source_job_id="102",
        title="AI Engineer",
        company_name="Stripe",
        apply_url="https://boards.greenhouse.io/stripe/jobs/102",
        raw_location="Remote",
        workplace_type=WorkplaceType.REMOTE,
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
    stmt = select(JobListing).where(
        JobListing.ats_provider == "greenhouse",
        JobListing.ats_board_slug == "stripe",
    )
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
        JobListing.ats_provider == "greenhouse",
        JobListing.ats_board_slug == "stripe",
        JobListing.source_job_id == "101",
    )
    db_job_101 = (await db_session.execute(stmt_101)).scalar_one()
    assert db_job_101.status == ListingStatus.CLOSED

    stmt_102 = select(JobListing).where(
        JobListing.ats_provider == "greenhouse",
        JobListing.ats_board_slug == "stripe",
        JobListing.source_job_id == "102",
    )
    db_job_102 = (await db_session.execute(stmt_102)).scalar_one()
    assert db_job_102.status == ListingStatus.ACTIVE


@pytest.mark.asyncio
async def test_multi_location_job_consolidation_into_canonical_listing(
    db_session: AsyncSession,
) -> None:
    poland_job = DiscoveredJobDTO(
        ats_provider="greenhouse",
        ats_board_slug="affirm",
        source_job_id="affirm-poland-101",
        title="Senior Software Engineer, Mobile (Repayment UX)",
        company_name="Affirm",
        apply_url="https://boards.greenhouse.io/affirm/jobs/101",
        raw_location="Remote Poland",
        city=None,
        state_province_code=None,
        country_code="PL",
        salary_range="240,000 - 300,000 PLN",
        raw_description="React Native and mobile payments architecture in Poland.",
    )
    spain_job = DiscoveredJobDTO(
        ats_provider="greenhouse",
        ats_board_slug="affirm",
        source_job_id="affirm-spain-102",
        title="Senior Software Engineer, Mobile (Repayment UX)",
        company_name="Affirm",
        apply_url="https://boards.greenhouse.io/affirm/jobs/102",
        raw_location="Remote Spain",
        city="Madrid",
        state_province_code=None,
        country_code="ES",
        salary_range="€65,000 - €85,000",
        raw_description="React Native and mobile payments architecture in Spain.",
    )

    fake_adapter = FakeGreenhouseAdapter([poland_job, spain_job])
    service = BoardSyncService(db_session)
    service.register_adapter(ATSProvider.GREENHOUSE, fake_adapter)

    # Sync board containing both location variants
    run = await service.sync_board("greenhouse", "affirm")
    assert run.status == "success"
    assert run.fetched_count == 2
    # The first one is created as new, the second one is consolidated as updated
    assert run.new_count == 1
    assert run.updated_count == 1

    # Verify only ONE row exists in JobListing table for this requisition
    stmt = select(JobListing).where(
        JobListing.ats_provider == "greenhouse",
        JobListing.ats_board_slug == "affirm",
    )
    listings = (await db_session.execute(stmt)).scalars().all()
    assert len(listings) == 1

    job = listings[0]
    assert "Remote Poland" in job.raw_location
    assert "Remote Spain" in job.raw_location
    assert job.canonical_fingerprint is not None

    # Verify location_postings preserved all individual location entries & apply URLs
    assert len(job.location_postings) == 2
    assert job.location_postings[0]["location"] == "Remote Poland"
    assert (
        job.location_postings[0]["apply_url"]
        == "https://boards.greenhouse.io/affirm/jobs/101"
    )
    assert job.location_postings[0]["is_primary"] is True

    assert job.location_postings[1]["location"] == "Remote Spain"
    assert (
        job.location_postings[1]["apply_url"]
        == "https://boards.greenhouse.io/affirm/jobs/102"
    )
    assert job.location_postings[1]["is_primary"] is False
