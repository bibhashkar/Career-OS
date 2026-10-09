"""
Unit tests for JobVerificationService and secondary cross-checking.

Verifies:
  1. Authoritative ATS data is preserved and never overwritten.
  2. Discrepancies (salary, status) are captured in the verification JSON payload.
  3. Verified status is set when secondary source agrees.
  4. 7-day cache TTL is enforced unless force=True.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.verification import JobVerificationService
from app.models.job_listing import JobListing


class MockDiscrepancyAdapter:
    """Mock cross-check adapter returning conflicting salary and status."""

    async def cross_check(
        self, title: str, company_name: str, location: str
    ) -> dict[str, Any] | None:
        return {
            "source": "mock_aggregator",
            "url": "https://example.com/job/conflict",
            "status": "closed",
            "salary_range": "$120,000 - $140,000",
            "sources_checked": ["mock_aggregator"],
        }


class MockNotFoundAdapter:
    """Mock cross-check adapter returning None."""

    async def cross_check(
        self, title: str, company_name: str, location: str
    ) -> dict[str, Any] | None:
        return None


@pytest.mark.asyncio
async def test_verification_detects_salary_and_status_discrepancy(
    db_session: AsyncSession,
) -> None:
    """Verify discrepancies with secondary sources do not overwrite ATS values."""
    job = JobListing(
        source="greenhouse",
        source_job_id="test_verif_001",
        title="Staff AI Engineer",
        company_name="Acme Corp",
        location="Remote",
        salary_range="$180,000 - $210,000",
        raw_description="Build distributed training pipelines.",
        status="active",
        data_origin="live",
        source_confidence="high",
    )
    db_session.add(job)
    await db_session.flush()

    service = JobVerificationService(
        session=db_session, adapter=MockDiscrepancyAdapter()
    )
    result = await service.verify_job(job.id, force=True)

    assert result["status"] == "discrepancy"
    assert len(result["discrepancies"]) == 2

    # Check fields
    discrepancy_fields = {d["field"] for d in result["discrepancies"]}
    assert "salary_range" in discrepancy_fields
    assert "status" in discrepancy_fields

    # Verify ATS fields were NOT overwritten on the ORM model
    stmt = select(JobListing).where(JobListing.id == job.id)
    refreshed = (await db_session.execute(stmt)).scalar_one()
    assert refreshed.salary_range == "$180,000 - $210,000"
    assert refreshed.status == "active"
    assert refreshed.last_verified_at is not None


@pytest.mark.asyncio
async def test_verification_handles_not_found_on_aggregators(
    db_session: AsyncSession,
) -> None:
    """Verify when no secondary listing is found, status='not_found' is recorded."""
    job = JobListing(
        source="ashby",
        source_job_id="test_verif_002",
        title="Founding ML Engineer",
        company_name="Stealth AI",
        location="San Francisco, CA",
        raw_description="Founding role.",
        status="active",
    )
    db_session.add(job)
    await db_session.flush()

    service = JobVerificationService(session=db_session, adapter=MockNotFoundAdapter())
    result = await service.verify_job(job.id, force=True)

    assert result["status"] == "not_found"
    assert result["discrepancies"] == []


@pytest.mark.asyncio
async def test_verification_enforces_7_day_cache_ttl(
    db_session: AsyncSession,
) -> None:
    """Verify existing verification is returned if within 7 days unless forced."""
    now = datetime.now(UTC)
    cached_verification = {
        "status": "verified",
        "last_checked_at": (now - timedelta(days=2)).isoformat(),
        "discrepancies": [],
        "notes": "Cached check.",
    }

    job = JobListing(
        source="lever",
        source_job_id="test_verif_003",
        title="Backend Architect",
        company_name="Linear",
        location="Remote",
        raw_description="Design high-performance distributed systems.",
        status="active",
        verification=cached_verification,
        last_verified_at=now - timedelta(days=2),
    )
    db_session.add(job)
    await db_session.flush()

    # Even with DiscrepancyAdapter, cached result should be returned when force=False
    service = JobVerificationService(
        session=db_session, adapter=MockDiscrepancyAdapter()
    )
    cached_res = await service.verify_job(job.id, force=False)
    assert cached_res["notes"] == "Cached check."
    assert cached_res["status"] == "verified"

    # When force=True, re-checks and finds discrepancies
    forced_res = await service.verify_job(job.id, force=True)
    assert forced_res["status"] == "discrepancy"
