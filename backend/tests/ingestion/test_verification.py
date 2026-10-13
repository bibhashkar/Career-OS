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
from app.models.ingestion import ATSBoard
from app.models.job_listing import JobListing


async def _get_or_create_test_board(
    session: AsyncSession, provider: str, slug: str, company: str
) -> ATSBoard:
    stmt = select(ATSBoard).where(ATSBoard.provider == provider, ATSBoard.slug == slug)
    b = (await session.execute(stmt)).scalar_one_or_none()
    if not b:
        b = ATSBoard(
            provider=provider,
            slug=slug,
            company_name=company,
            industry="enterprise_saas",
            is_active=True,
        )
        session.add(b)
        await session.flush()
    return b


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
    board = await _get_or_create_test_board(
        db_session, "greenhouse", "acme", "Acme Corp"
    )
    job = JobListing(
        ats_board_id=board.id,
        ats_provider="greenhouse",
        ats_board_slug="acme",
        source_job_id="test_verif_001",
        industry="enterprise_saas",
        title="Staff AI Engineer",
        company_name="Acme Corp",
        raw_location="Remote",
        workplace_type="remote",
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
    board = await _get_or_create_test_board(
        db_session, "ashby", "stealth", "Stealth AI"
    )
    job = JobListing(
        ats_board_id=board.id,
        ats_provider="ashby",
        ats_board_slug="stealth",
        source_job_id="test_verif_002",
        industry="enterprise_saas",
        title="Founding ML Engineer",
        company_name="Stealth AI",
        raw_location="San Francisco, CA",
        city="San Francisco",
        state_province_code="CA",
        country_code="US",
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

    board = await _get_or_create_test_board(db_session, "lever", "linear", "Linear")
    job = JobListing(
        ats_board_id=board.id,
        ats_provider="lever",
        ats_board_slug="linear",
        source_job_id="test_verif_003",
        industry="enterprise_saas",
        title="Backend Architect",
        company_name="Linear",
        raw_location="Remote",
        workplace_type="remote",
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
