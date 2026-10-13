"""
Unit tests for Tier-1 ATS adapters (Greenhouse, Lever, Ashby) with golden fixtures.
"""

from pathlib import Path

import httpx
import pytest

from app.ingestion.adapters.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter

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
