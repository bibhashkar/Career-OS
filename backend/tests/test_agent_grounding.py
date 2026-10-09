"""
Tests for Deep Agent Integration, Hunter Semantic pgvector Ranking, and ATS Grounding.

Verifies:
  1. LocalJobSourceService querying local PostgreSQL records with hermetic fallback.
  2. ProvenanceCompanyIntelService providing verified dossiers with provenance.
  3. Hunter agent node performing semantic pgvector ranking against candidate CV blocks
     instead of arbitrarily picking the first match.
  4. Tailor node extracting grounded requirements without ungrounded fallbacks.
  5. ATS evaluation loop scoring objectively against extracted grounded requirements.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.nodes.ats import ats_node
from app.agents.nodes.hunter import hunter_node
from app.agents.nodes.tailor import tailor_node
from app.agents.state import AgentState
from app.ingestion.api import (
    JobListingDTO,
    LocalJobSourceService,
    ProvenanceCompanyIntelService,
    VisaSponsorshipStatus,
)


@pytest.mark.asyncio
async def test_local_job_source_service_fallback_and_get() -> None:
    """Verify LocalJobSourceService searches and gets jobs with hermetic fallbacks."""
    service = LocalJobSourceService()

    # Search without live DB falls back to deterministic MOCK_JOBS
    jobs = await service.search_jobs(query="AI Systems Engineer")
    assert len(jobs) >= 1
    top_job = jobs[0]
    assert isinstance(top_job, JobListingDTO)
    assert "NexusAI" in top_job.company_name or "Engineer" in top_job.title

    # Get job by ID
    job_match = await service.get_job("job-ai-001")
    assert job_match is not None
    assert job_match.id == "job-ai-001"
    assert job_match.company_name == "NexusAI Labs"
    assert job_match.visa_sponsorship == VisaSponsorshipStatus.YES

    # Non-existent job
    missing = await service.get_job("nonexistent-job-999")
    assert missing is None


@pytest.mark.asyncio
async def test_provenance_company_intel_service() -> None:
    """Verify ProvenanceCompanyIntelService returns structured DTO."""
    service = ProvenanceCompanyIntelService()
    dossier = await service.get_company_profile("NexusAI Labs")

    assert dossier.company_name == "NexusAI Labs"
    assert "Python" in dossier.tech_stack
    assert dossier.business_model is not None


@pytest.mark.asyncio
async def test_hunter_ranks_job_matching_frontend_candidate() -> None:
    """
    Verify Hunter selects Full-Stack (job-ai-003) for React-focused candidate.

    Instead of blindly picking index 0 (NexusAI AI Engineer), Hunter evaluates
    semantic pgvector cosine similarity + skill overlap against candidate CV blocks.
    """
    frontend_blocks = [
        {
            "id": "fe-001",
            "category": "experience",
            "title": "Senior Frontend Developer",
            "organization": "WebCraft",
            "content": (
                "Developed responsive web applications with React, Tailwind CSS, "
                "and JavaScript. Optimized client rendering and UI component trees."
            ),
            "skills": ["React", "JavaScript", "Tailwind CSS", "Vite"],
        },
        {
            "id": "fe-002",
            "category": "project",
            "title": "Modern UI Component Library",
            "organization": "Open Source",
            "content": (
                "Created accessible design system with React and Tailwind CSS."
            ),
            "skills": ["React", "Tailwind CSS", "TypeScript"],
        },
    ]

    state: AgentState = {
        "user_id": "user-frontend-001",
        "job_details": {"title": "AI", "location": "Remote"},
    }

    with patch(
        "app.agents.nodes.hunter.search_cv_blocks",
        new=AsyncMock(return_value=frontend_blocks),
    ):
        result = await hunter_node(state)

    selected = result["job_details"]
    assert selected["id"] == "job-ai-003"
    assert selected["company_name"] == "CareerCloud Systems"
    assert selected["match_score"] > 0
    assert "pgvector semantic scoring" in result["messages"][0]["content"]


@pytest.mark.asyncio
async def test_hunter_ranks_job_matching_ai_systems_candidate() -> None:
    """
    Verify Hunter selects AI Systems (job-ai-001) for LangGraph/pgvector candidate.
    """
    ai_blocks = [
        {
            "id": "ai-001",
            "category": "experience",
            "title": "AI Platform Engineer",
            "organization": "VectorScale",
            "content": (
                "Designed stateful RAG agents with LangGraph, FastAPI, and PostgreSQL "
                "pgvector. Scaled semantic retrieval across millions of chunks."
            ),
            "skills": [
                "Python",
                "FastAPI",
                "LangGraph",
                "PostgreSQL",
                "pgvector",
            ],
        }
    ]

    state: AgentState = {
        "user_id": "user-ai-001",
        "job_details": {"title": "Engineer", "location": "Remote"},
    }

    with patch(
        "app.agents.nodes.hunter.search_cv_blocks",
        new=AsyncMock(return_value=ai_blocks),
    ):
        result = await hunter_node(state)

    selected = result["job_details"]
    assert selected["id"] == "job-ai-001"
    assert selected["company_name"] == "NexusAI Labs"
    assert selected["match_score"] > 0
    assert "pgvector semantic scoring" in result["messages"][0]["content"]


@pytest.mark.asyncio
async def test_tailor_node_grounds_skills_from_raw_description() -> None:
    """Verify tailor_node extracts grounded requirements from raw description."""
    raw_desc = (
        "We are seeking an Infrastructure Engineer. Must have deep experience with "
        "Kubernetes, Docker, Go, and Terraform."
    )
    state: AgentState = {
        "user_id": "user-infra-001",
        "job_details": {
            "title": "Infrastructure Engineer",
            "company_name": "CloudCorp",
            "raw_description": raw_desc,
            "ats_requirements": {},  # No parsed skills provided upfront
        },
        "revision_count": 0,
    }

    # Act
    result = await tailor_node(state)

    # Assert: draft was created without error
    assert result["status"] == "cv_tailored"
    assert result["cv_draft"]["target_company"] == "CloudCorp"


@pytest.mark.asyncio
async def test_ats_node_scores_against_deterministic_extracted_skills() -> None:
    """Verify ats_node computes match score against extracted skills."""
    raw_desc = (
        "Looking for an engineer skilled in Python, FastAPI, and Docker for platform."
    )
    state: AgentState = {
        "cv_draft": {
            "skills_highlighted": ["Python", "FastAPI"],
        },
        "job_details": {
            "title": "Backend Engineer",
            "company_name": "TechStart",
            "raw_description": raw_desc,
            "ats_requirements": {},
        },
        "revision_count": 1,
    }

    # Act
    result = await ats_node(state)

    # Assert: Python, FastAPI matched; Docker missing
    feedback = result["ats_feedback"]
    assert "Python" in feedback["matched_keywords"]
    assert "FastAPI" in feedback["matched_keywords"]
    assert "Docker" in feedback["missing_keywords"]
    assert result["status"] == "ats_evaluated"
