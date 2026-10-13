"""
Integration tests for Phase 6 Job Ingestion and Search API endpoints.

Verifies:
  1. POST /api/jobs/search includes provenance and verification fields.
  2. POST /api/jobs/ingest-url ingests supported ATS jobs and blocks SSRF.
  3. POST /api/jobs/paste-text extracts requirements and stores manual jobs.
  4. POST /api/companies/{company_name}/refresh enforces 1-hour cooldown.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import DiscoveredJobDTO
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def patch_db(
    monkeypatch: pytest.MonkeyPatch,
    db_session: AsyncSession,
) -> None:
    @asynccontextmanager
    async def _mock_context():
        yield db_session

    monkeypatch.setattr("app.api.jobs.get_session_context", _mock_context)
    monkeypatch.setattr(
        "app.agents.tools.company_intel.get_session_context", _mock_context
    )


@pytest.mark.asyncio
async def test_search_jobs_returns_provenance_metadata() -> None:
    """Verify search response attachments include provenance and status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/jobs/search",
            json={
                "query": "Systems Engineer",
                "location": "Remote",
                "visa_required": False,
            },
        )

    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    first_job = data["jobs"][0]
    assert "data_origin" in first_job
    assert "source_confidence" in first_job
    assert "verification" in first_job
    assert "visa_sponsorship" in first_job


@pytest.mark.asyncio
async def test_search_jobs_empty_query_returns_empty_list_200() -> None:
    """Verify empty query and location returns 200 with zero results without 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/jobs/search",
            json={
                "query": "",
                "location": "",
                "visa_required": False,
            },
        )

    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 0
    assert data["jobs"] == []


@pytest.mark.asyncio
async def test_ingest_url_blocks_ssrf_and_unsupported_urls() -> None:
    """Verify arbitrary web hosts and private IPs are rejected on direct URL import."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Non-ATS external page
        res = await client.post(
            "/api/jobs/ingest-url",
            json={"url": "https://example.com/careers/engineering-lead"},
        )
        assert res.status_code == 400
        assert "Direct URL ingestion supports Greenhouse" in res.json()["detail"]

        # Cloud metadata SSRF attempt
        res_ssrf = await client.post(
            "/api/jobs/ingest-url",
            json={"url": "http://169.254.169.254/latest/meta-data"},
        )
        assert res_ssrf.status_code == 400


@pytest.mark.asyncio
async def test_ingest_url_success_with_canonical_ats() -> None:
    """Verify valid ATS job posting URL is ingested and returns 201 Created."""
    mock_dto = DiscoveredJobDTO(
        source="greenhouse:stripe",
        source_job_id="1234567",
        title="Staff Infrastructure Engineer",
        company_name="Stripe",
        apply_url="https://boards.greenhouse.io/stripe/jobs/1234567",
        location="Remote",
        salary_range="$220,000 - $260,000",
        raw_description="Python, Kubernetes, and distributed consensus.",
    )

    with patch(
        "app.ingestion.adapters.ats.GreenhouseAdapter.fetch_job_detail",
        new=AsyncMock(return_value=mock_dto),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/jobs/ingest-url",
                json={"url": "https://boards.greenhouse.io/stripe/jobs/1234567"},
            )

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    assert data["job"]["title"] == "Staff Infrastructure Engineer"
    assert data["job"]["company_name"] == "Stripe"
    assert data["job"]["data_origin"] == "live"


@pytest.mark.asyncio
async def test_paste_job_text_creates_manual_listing() -> None:
    """Verify pasting job description text stores as data_origin='manual'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/jobs/paste-text",
            json={
                "title": "Principal AI Systems Architect",
                "company_name": "DeepScale Systems",
                "location": "San Francisco, CA",
                "salary_range": "$250,000 - $300,000",
                "raw_description": (
                    "We require 8+ years experience in Python and PyTorch. "
                    "Visa sponsorship is available for qualified candidates."
                ),
            },
        )

    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    job = data["job"]
    assert job["data_origin"] == "manual"
    assert job["company_name"] == "DeepScale Systems"
    assert "Python" in job["ats_requirements"]["required_skills"]
    assert job["visa_sponsorship"] == "yes"


@pytest.mark.asyncio
async def test_company_intel_refresh_and_cooldown() -> None:
    """Verify company intel refresh enforces 1-hour cooldown."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First refresh: triggers provider
        res1 = await client.post("/api/jobs/companies/Stripe/refresh")
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "refreshed"
        assert data1["refreshed"] is True

        # Second refresh immediately: returns cooldown
        res2 = await client.post("/api/jobs/companies/Stripe/refresh")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "cooldown"
        assert data2["refreshed"] is False
        assert "Cooldown" in data2["message"]
