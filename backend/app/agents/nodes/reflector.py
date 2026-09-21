"""Reflector agent node synthesizing candidate feedback into persistent weights."""

from typing import Any

from app.agents.state import AgentState


async def reflector_node(state: AgentState) -> dict[str, Any]:
    """Analyze feedback logs and generate updated tone and prompt weight directives."""
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
