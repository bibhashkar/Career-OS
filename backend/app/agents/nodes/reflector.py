"""
Reflector agent node synthesizing candidate feedback into quantitative directives.

Static agent prompts fail to adapt to individual candidate learning styles and
career seniorities. The reflector node closes the learning loop: it evaluates
qualitative candidate reviews (e.g., "focus more on distributed consensus" or
"make questions shorter and more conversational") and computes numeric prompt
weight adjustments.

Feedback Reflection Cycle & Structured Output:
  1. Candidate submits feedback via ``POST /api/feedback``.
  2. ``reflector_app`` runs ``reflector_node`` against the candidate's thread.
  3. LLM structured output (via ``ReflectorDirectiveSchema``) derives prompt
     hyperparameters (technical_depth, brevity, style).
  4. Updated adjustments are recorded in ``feedback_logs`` (and persisted to
     PostgreSQL ``feedback_log``).
  5. Subsequent sessions read these weights in ``profiler_node`` to customize
     all agent prompts automatically.
"""

import asyncio
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_llm
from app.agents.state import AgentState


class ReflectorDirectiveSchema(BaseModel):
    """Structured prompt weights extracted from qualitative user feedback."""

    technical_depth: float = Field(
        default=0.85,
        description="Technical depth (0.0 to 1.0). Higher values ask deeper questions.",
    )
    brevity: float = Field(
        default=0.80,
        description="Brevity (0.0 to 1.0). Higher values yield shorter messages.",
    )
    style: str = Field(
        default="direct",
        description="Style: 'direct', 'conversational', 'executive', or 'rigorous'.",
    )
    rationale: str = Field(
        default="Balanced directives based on user feedback.",
        description="Explanation of why adjustments were chosen.",
    )


async def reflector_node(state: AgentState) -> dict[str, Any]:
    """
    Analyze candidate feedback and compute updated agent prompt weights.

    Reads:
      - ``feedback_logs``: The historical list of user reviews.
      - ``user_feedback``: Immediate user review if supplied at top level.

    Writes:
      - ``feedback_logs``: Appends an enriched log containing computed adjustments.
      - ``status``: Set to ``"feedback_reflected"``.
      - ``messages``: System log documenting the updated directive weights.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update containing the synthesized prompt adjustments.
    """
    raw_input = state.get("user_feedback")
    thread_id = ""
    if raw_input:
        original_feedback = raw_input
    else:
        feedback_logs = state.get("feedback_logs", [])
        recent_feedback = feedback_logs[-1] if feedback_logs else {}
        original_feedback = recent_feedback.get("user_feedback", "")
        thread_id = recent_feedback.get("thread_id", "")

    feedback_text = original_feedback.lower()

    # Baseline heuristic fallback for offline tests and network resiliency
    fallback_depth = 0.85
    fallback_brevity = 0.80
    fallback_style = "direct"

    if "more technical" in feedback_text or "system design" in feedback_text:
        fallback_depth = 0.95
    if "concise" in feedback_text or "shorter" in feedback_text:
        fallback_brevity = 0.95
    if "soft skills" in feedback_text or "behavioral" in feedback_text:
        fallback_style = "conversational"
        fallback_depth = 0.70

    mock_json = json.dumps(
        {
            "technical_depth": fallback_depth,
            "brevity": fallback_brevity,
            "style": fallback_style,
            "rationale": "Feedback analyzed for coaching adaptation.",
        }
    )

    llm = get_llm(
        temperature=0.1,
        default_mock_responses=[mock_json],
    )

    system_prompt = (
        "You are an AI pedagogy and calibration engine. Analyze qualitative "
        "user feedback from a technical mock interview and produce quantitative "
        "prompt weight adjustments (technical_depth: 0.0-1.0, brevity: 0.0-1.0, "
        "style: direct/conversational/executive/rigorous)."
    )
    user_prompt = f'Candidate Review: "{original_feedback}"'

    resolved_depth = fallback_depth
    resolved_brevity = fallback_brevity
    resolved_style = fallback_style

    try:
        chain = llm.with_structured_output(ReflectorDirectiveSchema)
        res = await asyncio.wait_for(
            chain.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            ),
            timeout=10.0,
        )
        if isinstance(res, ReflectorDirectiveSchema):
            resolved_depth = round(max(0.0, min(1.0, res.technical_depth)), 2)
            resolved_brevity = round(max(0.0, min(1.0, res.brevity)), 2)
            resolved_style = res.style or fallback_style
    except Exception:
        resolved_depth = fallback_depth
        resolved_brevity = fallback_brevity
        resolved_style = fallback_style

    adjustments: dict[str, Any] = {
        "technical_depth": resolved_depth,
        "brevity": resolved_brevity,
        "style": resolved_style,
    }

    updated_log = {
        "thread_id": thread_id,
        "user_feedback": original_feedback,
        "prompt_weight_adjustments": adjustments,
        "applied": True,
    }

    return {
        "feedback_logs": [updated_log],
        "status": "feedback_reflected",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Reflector updated directives: "
                    f"depth={adjustments['technical_depth']}, "
                    f"brevity={adjustments['brevity']}, "
                    f"style='{adjustments['style']}'."
                ),
            }
        ],
    }
