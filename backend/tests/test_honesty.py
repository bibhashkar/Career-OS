"""Unit tests validating Phase 0a honesty fixes.

Verifies that:
  1. Default GEMINI_MODEL is not the deprecated/shut-down gemini-1.5-flash.
  2. ats_node does not default required skills to ['Python', 'FastAPI'].
  3. MOCK_JOBS and MOCK_DOSSIERS are explicitly tagged with data_origin='demo'.
  4. fetch_company_intel does not invent fake news articles or tech stacks.
"""

import pytest

from app.agents.nodes.ats import ats_node
from app.agents.state import AgentState
from app.agents.tools.company_intel import MOCK_DOSSIERS, fetch_company_intel
from app.agents.tools.job_search import MOCK_JOBS, search_jobs
from app.core.config import settings


def test_gemini_model_is_not_deprecated() -> None:
    """Verify GEMINI_MODEL does not point to retired gemini-1.5-flash."""
    assert "1.5-flash" not in settings.GEMINI_MODEL
    assert settings.GEMINI_MODEL == "gemini-2.5-flash"


def test_mock_jobs_are_tagged_as_demo() -> None:
    """Verify built-in mock jobs are explicitly labeled with data_origin='demo'."""
    for job in MOCK_JOBS:
        assert job.get("data_origin") == "demo"


def test_mock_dossiers_are_tagged_as_demo() -> None:
    """Verify built-in mock dossiers are explicitly labeled with data_origin='demo'."""
    for name, dossier in MOCK_DOSSIERS.items():
        assert dossier.get("data_origin") == "demo", (
            f"Dossier {name} missing data_origin demo"
        )


@pytest.mark.asyncio
async def test_search_jobs_demo_results_have_demo_origin() -> None:
    """Verify search_jobs offline fallback preserves data_origin='demo'."""
    results = await search_jobs(query="Systems Engineer", location="Remote")
    assert len(results) > 0
    for job in results:
        assert job.get("data_origin") == "demo"


@pytest.mark.asyncio
async def test_ats_node_does_not_fabricate_skills_when_empty() -> None:
    """Verify ats_node does not invent requirements when none specified."""
    state: AgentState = {
        "cv_draft": {
            "skills_highlighted": ["Kubernetes", "Terraform"],
            "professional_summary": "Cloud infrastructure engineer.",
        },
        "job_details": {
            "title": "Site Reliability Engineer",
            "ats_requirements": {},  # No required_skills specified
        },
        "revision_count": 1,
    }
    result = await ats_node(state)
    assert result["status"] == "ats_evaluated"
    feedback = result["ats_feedback"]

    # Must NOT have defaulted to ['Python', 'FastAPI']
    assert "Python" not in feedback["missing_keywords"]
    assert "FastAPI" not in feedback["missing_keywords"]
    assert feedback["matched_keywords"] == []
    assert feedback["missing_keywords"] == []


@pytest.mark.asyncio
async def test_company_intel_does_not_fabricate_news_or_stack() -> None:
    """Verify unknown company intel does not invent fake publications."""
    dossier = await fetch_company_intel("Aegis Dynamic Testing Corp")
    assert dossier["company_name"] == "Aegis Dynamic Testing Corp"
    assert dossier.get("data_origin") == "inferred"

    # Must not contain fabricated fake news
    for news in dossier.get("recent_news", []):
        assert "expands engineering for AI" not in news.get("title", "")
        assert "Industry Journal" not in news.get("source", "")
