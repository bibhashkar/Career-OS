"""CV generation and ATS evaluation loop API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, status
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agents.graph import pipeline_app
from app.agents.state import AgentState

router = APIRouter(prefix="/api/cv", tags=["CV"])


class CVGenerateRequest(BaseModel):
    """Payload for triggering CV tailoring and iterative ATS evaluation."""

    job_id: str = Field(..., examples=["job-ai-001"])
    user_id: str | None = Field(None, examples=["user-123"])
    title: str | None = Field(
        "Senior AI Systems Engineer", examples=["Senior AI Engineer"]
    )
    company_name: str | None = Field("NexusAI Labs", examples=["NexusAI Labs"])
    required_skills: list[str] = Field(
        default_factory=lambda: ["Python", "FastAPI", "LangGraph", "pgvector"]
    )


class CVGenerateResponse(BaseModel):
    """Response payload containing generated CV draft and ATS scorecard."""

    job_id: str
    cv_draft: dict[str, Any]
    ats_score: float
    ats_feedback: dict[str, Any]
    revision_count: int
    passed: bool


@router.post(
    "/generate",
    response_model=CVGenerateResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_tailored_cv(
    request: CVGenerateRequest,
) -> CVGenerateResponse:
    """Execute LangGraph CV tailoring and cyclic ATS evaluation sequence."""
    initial_state: AgentState = {
        "user_id": request.user_id or str(uuid.uuid4()),
        "current_job_id": request.job_id,
        "job_details": {
            "id": request.job_id,
            "title": request.title,
            "company_name": request.company_name,
            "ats_requirements": {
                "required_skills": request.required_skills,
                "visa_sponsorship": True,
            },
        },
        "revision_count": 0,
    }

    thread_id = f"cv_gen_{request.job_id}_{uuid.uuid4().hex[:8]}"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    final_state = await pipeline_app.ainvoke(initial_state, config=config)

    ats_score = final_state.get("ats_score", 0.0)
    return CVGenerateResponse(
        job_id=request.job_id,
        cv_draft=final_state.get("cv_draft") or {},
        ats_score=ats_score,
        ats_feedback=final_state.get("ats_feedback") or {},
        revision_count=final_state.get("revision_count", 1),
        passed=ats_score >= 75.0,
    )
