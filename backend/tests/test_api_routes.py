"""Integration tests for Career-OS REST endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.graph import interview_app
from app.main import app


@pytest.mark.asyncio
async def test_jobs_search_endpoint() -> None:
    """Verify POST /api/jobs/search returns enriched jobs with company dossiers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "query": "Senior AI Systems Engineer",
            "location": "Remote",
            "visa_required": True,
        }
        response = await client.post("/api/jobs/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    first_job = data["jobs"][0]
    assert "company_dossier" in first_job
    assert "tech_stack" in first_job["company_dossier"]


@pytest.mark.asyncio
async def test_cv_generate_endpoint() -> None:
    """Verify POST /api/cv/generate returns tailored CV draft and ATS score."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "job_id": "job-ai-001",
            "title": "Senior AI Systems Engineer",
            "company_name": "NexusAI Labs",
            "required_skills": ["Python", "FastAPI", "LangGraph", "pgvector"],
        }
        response = await client.post("/api/cv/generate", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job-ai-001"
    assert "cv_draft" in data
    assert data["ats_score"] >= 70.0
    assert data["revision_count"] >= 1
    assert "ats_feedback" in data


@pytest.mark.asyncio
async def test_feedback_endpoint() -> None:
    """Verify POST /api/feedback synthesizes prompt weight adjustments."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "thread_id": "test_thread_api_feedback",
            "user_feedback": "Please emphasize system design and scalability.",
        }
        response = await client.post("/api/feedback", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "test_thread_api_feedback"
    assert data["status"] == "weights_updated"
    assert data["prompt_weight_adjustments"].get("technical_depth") == 0.95


@pytest.mark.asyncio
async def test_feedback_does_not_pollute_interview_thread_state() -> None:
    """Verify feedback submissions never overwrite or corrupt interview state."""
    thread_id = "test_thread_isolation_ws_999"
    int_config = {"configurable": {"thread_id": thread_id}}

    # Initialize an active interview session
    await interview_app.ainvoke(
        {
            "company_dossier": {"company_name": "NexusAI Labs"},
            "messages": [],
        },
        config=int_config,
    )

    # Submit feedback referencing the same thread_id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "thread_id": thread_id,
            "user_feedback": "Make responses shorter and more concise.",
        }
        resp = await client.post("/api/feedback", json=payload)
    assert resp.status_code == 200

    # Ensure interview checkpoint is unchanged and not overwritten by reflector
    state = await interview_app.aget_state(int_config)
    assert state is not None
    assert len(state.values.get("interview_history", [])) == 1
    # Status should remain interview_active, not feedback_reflected
    assert state.values.get("status") == "interview_active"
