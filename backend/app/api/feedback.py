"""
User review and prompt weight reflection API endpoints.

This router manages candidate feedback ingestion. When a user completes a mock
interview or reviews a generated CV, they can provide qualitative input (e.g.
"ask harder questions", "be more concise").

Reflection Workflow:
  1. Frontend submits ``POST /api/feedback`` with ``thread_id`` and feedback text.
  2. The router structures an ``AgentState`` payload and invokes ``reflector_app``.
  3. The reflector node analyzes sentiment and keywords to tune hyperparameters
     (technical_depth, brevity, conversational style).
  4. The updated weights are returned and persisted, immediately influencing
     subsequent agent invocations within the thread.
"""

from typing import Any

from fastapi import APIRouter, status
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.agents.graph import reflector_app
from app.agents.state import AgentState

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """
    Payload for submitting user interview and coaching feedback.

    Attributes:
        thread_id: Conversational thread session to update.
        user_feedback: Qualitative critique or guidance from the candidate.
    """

    thread_id: str = Field(..., examples=["thread_interview_123"])
    user_feedback: str = Field(
        ...,
        min_length=3,
        examples=["Focus more heavily on distributed consensus and system design."],
    )


class FeedbackResponse(BaseModel):
    """
    Response confirming synthesized prompt weight adjustments.

    Attributes:
        thread_id: Thread session where adjustments were applied.
        prompt_weight_adjustments: Map of updated directive weights.
        status: Operation confirmation status string.
    """

    thread_id: str
    prompt_weight_adjustments: dict[str, Any]
    status: str


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Synthesize candidate feedback into updated agent prompt weights.

    Passes candidate review text to ``reflector_app``, which computes updated
    numeric weights for technical depth, brevity, and tone style.

    Args:
        request: Validated feedback payload with thread_id and text.

    Returns:
        FeedbackResponse containing the active weight adjustments.
    """
    state: AgentState = {
        "user_feedback": request.user_feedback,
    }

    # Namespace the thread to isolate reflector checkpoints from interview messages
    thread_id = f"reflector_{request.thread_id}"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    result = await reflector_app.ainvoke(state, config=config)

    logs = result.get("feedback_logs", [])
    last_log = logs[-1] if logs else {}

    return FeedbackResponse(
        thread_id=request.thread_id,
        prompt_weight_adjustments=last_log.get("prompt_weight_adjustments", {}),
        status="weights_updated",
    )
