"""Profiler agent node evaluating constraints, visa status, and tone directives."""

from typing import Any

from app.agents.state import AgentState


async def profiler_node(state: AgentState) -> dict[str, Any]:
    """Evaluate baseline user constraints and establish initial profile context."""
    user_id = state.get("user_id")
    job_details = state.get("job_details") or {}

    # Extract or provide sensible defaults for user constraints
    visa_required = False
    tone = {"style": "confident", "brevity": "high", "technical_depth": 0.85}

    if state.get("feedback_logs"):
        # Apply any reflected weights from previous sessions
        for log in state["feedback_logs"]:
            adjustments = log.get("prompt_weight_adjustments", {})
            tone.update(adjustments)

    return {
        "user_id": user_id,
        "status": "profile_evaluated",
        "job_details": job_details,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Profiler evaluated constraints. Visa required: {visa_required}. "
                    f"Active tone directives: {tone.get('style', 'balanced')}."
                ),
            }
        ],
    }
