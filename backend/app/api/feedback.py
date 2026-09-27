"""User review and prompt weight reflection API endpoints."""

from typing import Any

from fastapi import APIRouter, status
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agents.graph import reflector_app
from app.agents.state import AgentState

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """Payload for submitting user interview and coaching feedback."""

    thread_id: str = Field(..., examples=["thread_interview_123"])
    user_feedback: str = Field(
        ...,
        min_length=3,
        examples=["Focus more heavily on distributed consensus and system design."],
    )


class FeedbackResponse(BaseModel):
    """Response confirming synthesized prompt weight adjustments."""

    thread_id: str
    prompt_weight_adjustments: dict[str, Any]
    status: str


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Synthesize candidate feedback into updated agent prompt weights."""
    state: AgentState = {
        "feedback_logs": [
            {
                "thread_id": request.thread_id,
                "user_feedback": request.user_feedback,
            }
        ]
    }

    config: RunnableConfig = {"configurable": {"thread_id": request.thread_id}}
    result = await reflector_app.ainvoke(state, config=config)

    logs = result.get("feedback_logs", [])
    last_log = logs[-1] if logs else {}

    return FeedbackResponse(
        thread_id=request.thread_id,
        prompt_weight_adjustments=last_log.get("prompt_weight_adjustments", {}),
        status="weights_updated",
    )
