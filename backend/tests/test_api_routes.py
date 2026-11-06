"""Integration tests for Career-OS REST endpoints."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import interview_app
from app.core.auth import create_access_token
from app.core.database import get_db
from app.main import app
from app.models.user_account import CandidatePersona, UserAccount


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
    int_config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

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


@pytest.mark.asyncio
async def test_job_diagnostics_invalid_uuid() -> None:
    """Verify invalid job_id or persona_id UUID format returns HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid job_id
        res_job = await client.get("/api/jobs/invalid-uuid/diagnostics")
        assert res_job.status_code == 400
        assert "job_id" in res_job.json()["detail"]

        # Invalid persona_id
        valid_job_id = "00000000-0000-0000-0000-000000000001"
        res_persona = await client.get(
            f"/api/jobs/{valid_job_id}/diagnostics?persona_id=not-a-uuid"
        )
        assert res_persona.status_code == 400
        assert "persona_id" in res_persona.json()["detail"]


@pytest.mark.asyncio
async def test_job_diagnostics_unowned_persona_idor_rejected(
    db_session: AsyncSession,
) -> None:
    """Verify User B cannot run diagnostics against User A's persona (HTTP 404)."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    job_id = uuid.uuid4()
    persona_a_id = uuid.uuid4()

    # Create UserAccount A and persona A
    acc_a = UserAccount(
        id=user_a_id,
        email=f"alice-{user_a_id}@career-os.local",
        full_name="Alice User",
        visa_status="Citizen",
    )
    persona_a = CandidatePersona(
        id=persona_a_id,
        user_account_id=user_a_id,
        name="Alice Backend Persona",
        is_default=True,
    )
    db_session.add(acc_a)
    db_session.add(persona_a)
    await db_session.commit()

    token_b = create_access_token(user_id=str(user_b_id))

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/jobs/{job_id}/diagnostics?persona_id={persona_a_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Persona not found."
    finally:
        app.dependency_overrides.pop(get_db, None)
