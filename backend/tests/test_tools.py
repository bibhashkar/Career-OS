"""Unit tests for hermetic external tools (job search, intel, vector search)."""

import pytest

from app.agents.tools import fetch_company_intel, search_cv_blocks, search_jobs


@pytest.mark.asyncio
async def test_search_jobs_with_visa_filtering() -> None:
    """Verify job search filters by visa sponsorship when required."""
    results = await search_jobs(
        query="AI Systems Engineer",
        location="Remote",
        visa_sponsorship_required=True,
    )
    assert len(results) > 0
    for job in results:
        assert job["ats_requirements"]["visa_sponsorship"] is True


@pytest.mark.asyncio
async def test_fetch_company_intel_returns_structured_dossier() -> None:
    """Verify company intel tool returns tech stack, news, and business model."""
    dossier = await fetch_company_intel("NexusAI Labs")
    assert dossier["company_name"] == "NexusAI Labs"
    assert "Python" in dossier["tech_stack"]
    assert "LangGraph" in dossier["tech_stack"]
    assert len(dossier["recent_news"]) > 0


@pytest.mark.asyncio
async def test_search_cv_blocks_skill_matching() -> None:
    """Verify vector search helper ranks blocks matching required skills."""
    blocks = await search_cv_blocks(
        user_id=None,
        required_skills=["LangGraph", "pgvector"],
        limit=2,
    )
    assert len(blocks) == 2
    top_block = blocks[0]
    assert any(s in top_block["skills"] for s in ["LangGraph", "pgvector", "FastAPI"])
