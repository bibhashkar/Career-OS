"""
Reflector agent node synthesizing candidate feedback into quantitative directives.

Static agent prompts fail to adapt to individual candidate learning styles and
career seniorities. The reflector node closes the learning loop: it evaluates
qualitative candidate reviews (e.g., "focus more on distributed consensus" or
"make questions shorter and more conversational") and computes numeric prompt
weight adjustments.

Feedback Reflection Cycle:
  1. Candidate submits feedback via ``POST /api/feedback``.
  2. ``reflector_app`` runs ``reflector_node`` against the candidate's thread.
  3. Qualitative text is mapped to prompt hyperparameters (technical_depth,
     brevity, style).
  4. Updated adjustments are recorded in ``feedback_logs`` (and persisted to
     PostgreSQL ``feedback_log``).
  5. Subsequent sessions read these weights in ``profiler_node`` to customize
     all agent prompts automatically.
"""

from typing import Any

from app.agents.state import AgentState


async def reflector_node(state: AgentState) -> dict[str, Any]:
    """
    Analyze candidate feedback and compute updated agent prompt weights.

    Reads:
      - ``feedback_logs``: The historical list of user reviews.

    Writes:
      - ``feedback_logs``: Appends an enriched log containing computed adjustments.
      - ``status``: Set to ``"feedback_reflected"``.
      - ``messages``: System log documenting the updated directive weights.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update containing the synthesized prompt adjustments.
    """
    feedback_logs = state.get("feedback_logs", [])
    recent_feedback = feedback_logs[-1] if feedback_logs else {}
    feedback_text = recent_feedback.get("user_feedback", "").lower()

    # Determine prompt adjustments based on candidate feedback themes
    adjustments: dict[str, Any] = {
        "technical_depth": 0.85,
        "brevity": 0.8,
        "style": "direct",
    }

    if "more technical" in feedback_text or "system design" in feedback_text:
        adjustments["technical_depth"] = 0.95
    if "concise" in feedback_text or "shorter" in feedback_text:
        adjustments["brevity"] = 0.95
    if "soft skills" in feedback_text or "behavioral" in feedback_text:
        adjustments["style"] = "conversational"
        adjustments["technical_depth"] = 0.70

    updated_log = {
        "user_feedback": recent_feedback.get("user_feedback", ""),
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
