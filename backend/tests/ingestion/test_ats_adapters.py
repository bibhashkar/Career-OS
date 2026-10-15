"""
Unit tests for Tier-1 ATS adapters (Greenhouse, Lever, Ashby) with golden fixtures.
"""

from pathlib import Path

import httpx
import pytest

from app.ingestion.adapters.ats import (
    AshbyAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    SmartRecruitersAdapter,
    WorkableAdapter,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_greenhouse_adapter_parses_golden_fixture() -> None:
    fixture_content = (FIXTURES_DIR / "greenhouse_jobs.json").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture_content)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    adapter = GreenhouseAdapter(client=client)
    jobs = await adapter.fetch_board_jobs("stripe")

    assert len(jobs) == 2
    first = jobs[0]
    assert first.ats_provider == "greenhouse"
    assert first.ats_board_slug == "stripe"
    assert first.source_job_id == "101"
    assert first.title == "Senior Backend Engineer"
    assert first.city == "San Francisco"
    assert first.state_province_code == "CA"
    assert "We are seeking a Senior Backend Engineer" in first.raw_description
    assert "<p>" not in first.raw_description  # HTML safely stripped
    assert first.apply_url == "https://boards.greenhouse.io/stripe/jobs/101"

    second = jobs[1]
    assert second.source_job_id == "102"
    assert second.workplace_type == "remote"


@pytest.mark.asyncio
async def test_lever_adapter_parses_golden_fixture() -> None:
    fixture_content = (FIXTURES_DIR / "lever_jobs.json").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture_content)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    adapter = LeverAdapter(client=client)
    jobs = await adapter.fetch_board_jobs("postman")

    assert len(jobs) == 2
    first = jobs[0]
    assert first.ats_provider == "lever"
    assert first.ats_board_slug == "postman"
    assert first.source_job_id == "lever-job-001"
    assert first.title == "Staff Systems Engineer"
    assert first.city == "San Francisco"
    assert first.state_province_code == "CA"
    assert "Build fault-tolerant multi-agent pipelines" in first.raw_description
    assert first.apply_url == "https://jobs.lever.co/postman/lever-job-001/apply"


@pytest.mark.asyncio
async def test_ashby_adapter_parses_golden_fixture() -> None:
    fixture_content = (FIXTURES_DIR / "ashby_jobs.json").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=fixture_content)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    adapter = AshbyAdapter(client=client)
    jobs = await adapter.fetch_board_jobs("linear")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.ats_provider == "ashby"
    assert job.ats_board_slug == "linear"
    assert job.source_job_id == "ashby-job-001"
    assert job.title == "Principal Agent Architect"
    assert job.workplace_type == "remote"
    assert "<p>" not in job.raw_description
    assert "Architect autonomous systems" in job.raw_description


@pytest.mark.asyncio
async def test_workable_adapter_parses_golden_fixture() -> None:
    list_content = (FIXTURES_DIR / "workable_jobs.json").read_text()
    detail_content = (FIXTURES_DIR / "workable_detail.json").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        if "/jobs/WRK001" in str(request.url):
            return httpx.Response(200, text=detail_content)
        return httpx.Response(200, text=list_content)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    adapter = WorkableAdapter(client=client)
    jobs = await adapter.fetch_board_jobs("techcorp")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.ats_provider == "workable"
    assert job.ats_board_slug == "techcorp"
    assert job.source_job_id == "WRK001"
    assert job.title == "Senior Distributed Systems Engineer"
    assert job.city == "London"
    assert job.country_code == "GB"
    assert job.workplace_type == "hybrid"
    assert "event processing pipelines using Python and Kafka" in job.raw_description
    assert "<p>" not in job.raw_description
    assert job.visa_sponsorship == "yes"


@pytest.mark.asyncio
async def test_smartrecruiters_adapter_parses_golden_fixture() -> None:
    list_content = (FIXTURES_DIR / "smartrecruiters_jobs.json").read_text()
    detail_content = (FIXTURES_DIR / "smartrecruiters_detail.json").read_text()

    def handler(request: httpx.Request) -> httpx.Response:
        if "/postings/sr-job-001" in str(request.url):
            return httpx.Response(200, text=detail_content)
        return httpx.Response(200, text=list_content)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)

    adapter = SmartRecruitersAdapter(client=client)
    jobs = await adapter.fetch_board_jobs("deliveryhero")

    assert len(jobs) == 1
    job = jobs[0]
    assert job.ats_provider == "smartrecruiters"
    assert job.ats_board_slug == "deliveryhero"
    assert job.source_job_id == "sr-job-001"
    assert job.title == "Staff Infrastructure Architect"
    assert job.city == "Berlin"
    assert job.country_code == "DE"
    assert job.workplace_type == "hybrid"
    assert "cloud architecture on Kubernetes" in job.raw_description
    assert "<p>" not in job.raw_description
    assert job.visa_sponsorship == "yes"
