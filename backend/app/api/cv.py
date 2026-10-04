"""
CV generation and ATS evaluation loop API endpoints.

This router exposes the primary resume tailoring entry point. When a candidate
selects a target job listing from the React dashboard, the frontend submits a
``POST /api/cv/generate`` request.

Decoupled Architecture:
The router performs no LLM inference or vector math itself. It acts as a thin
HTTP transport layer: it builds an initial ``AgentState`` payload, assigns an
isolated execution ``thread_id``, and invokes the compiled LangGraph
``pipeline_app``. The pipeline runs profiler, hunter, intel, tailor, and ATS
nodes, cycling up to 3 times if necessary, before returning the final scorecard.
"""

import uuid
from typing import Any

from fastapi import APIRouter, status
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agents.graph import pipeline_app
from app.agents.state import AgentState

router = APIRouter(prefix="/api/cv", tags=["CV"])


class CVGenerateRequest(BaseModel):
    """
    Payload for triggering CV tailoring and iterative ATS evaluation.

    Attributes:
        job_id: Unique identifier of the target job listing.
        user_id: Optional candidate identifier; defaults to a generated UUID.
        title: Target role title to emphasize in professional summaries.
        company_name: Name of prospective employer for contextual tailoring.
        required_skills: Core technical competencies extracted from job description.
    """

    job_id: str = Field(..., examples=["job-ai-001"])
    user_id: str | None = Field(None, examples=["user-123"])
    title: str | None = Field(
        "Senior AI Systems Engineer", examples=["Senior AI Engineer"]
    )
    company_name: str | None = Field("NexusAI Labs", examples=["NexusAI Labs"])
    required_skills: list[str] = Field(
        default_factory=lambda: ["Python", "FastAPI", "LangGraph", "pgvector"]
    )
    visa_required: bool | None = Field(None, examples=[True])
    tone_directives: dict[str, Any] | None = Field(
        None, examples=[{"style": "executive", "brevity": "high"}]
    )


class CVGenerateResponse(BaseModel):
    """
    Response payload containing generated CV draft and ATS scorecard.

    Attributes:
        job_id: Identifier of the evaluated job listing.
        cv_draft: Tailored resume draft including professional summary and blocks.
        ats_score: Final compatibility percentage (0.0 to 100.0).
        ats_feedback: Keyword match diagnostics and recommended enhancements.
        revision_count: Number of cyclic tailoring iterations performed.
        passed: Boolean indicating whether the score achieved the >=75.0% threshold.
    """

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
    """
    Execute LangGraph CV tailoring and cyclic ATS evaluation sequence.

    Instantiates the pipeline agent graph, passing candidate constraints and
    job requirements. If the generated draft scores below 75% on keyword
    compatibility, the graph automatically loops back to ``tailor_node`` up
    to 3 times before returning the final optimized resume draft.

    Args:
        request: Validated job criteria and candidate identification.

    Returns:
        CVGenerateResponse containing the tailored draft and ATS scorecard.
    """
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
    if request.visa_required is not None:
        initial_state["visa_required"] = request.visa_required
    if request.tone_directives is not None:
        initial_state["tone_directives"] = request.tone_directives

    # Isolated thread identifier ensures state checkpoints do not collide
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
