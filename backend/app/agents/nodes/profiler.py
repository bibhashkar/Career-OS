"""
Profiler agent node establishing user constraints and stylistic directives.

As the entry point for the pipeline graph (START -> profiler), this node
evaluates baseline candidate parameters:
  - User identity and profile persistence.
  - Work authorization / visa constraints (H-1B, OPT, etc.).
  - Stylistic tone directives (brevity, confidence, technical depth).

Continuous Personalization:
If previous coaching or review feedback exists in ``feedback_logs``, the profiler
re-applies synthesized prompt weight adjustments. This ensures that user
preferences (such as "be more concise" or "ask more system design questions")
persist into new job applications and coaching sessions without manual re-entry.
"""

from typing import Any

from app.agents.state import AgentState


async def profiler_node(state: AgentState) -> dict[str, Any]:
    """
    Evaluate baseline user constraints and establish initial profile context.

    Reads:
      - ``user_id``: Candidate profile identifier.
      - ``job_details``: Initial job query context.
      - ``feedback_logs``: Prior reflected prompt weight adjustments.

    Writes:
      - ``user_id``: Validated candidate identifier.
      - ``job_details``: Standardized job parameters for downstream nodes.
      - ``status``: Set to ``"profile_evaluated"``.
      - ``messages``: System log documenting evaluated constraints and tone.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update establishing the initial execution profile.
    """
    user_id = state.get("user_id")
    job_details = state.get("job_details") or {}

    # Extract or provide sensible defaults for user constraints
    visa_required = state.get("visa_required", job_details.get("visa_required", False))
    tone: dict[str, Any] = {
        "style": "confident",
        "brevity": "high",
        "technical_depth": 0.85,
    }
    if state.get("tone_directives"):
        tone.update(state["tone_directives"])

    if state.get("feedback_logs"):
        # Apply any reflected weights from previous sessions
        for log in state["feedback_logs"]:
            adjustments = log.get("prompt_weight_adjustments", {})
            tone.update(adjustments)

    return {
        "user_id": user_id,
        "status": "profile_evaluated",
        "job_details": job_details,
        "visa_required": visa_required,
        "tone_directives": tone,
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
