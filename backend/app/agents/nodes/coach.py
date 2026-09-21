"""Coach agent node managing stateful, interactive mock interview simulations."""

from typing import Any

from app.agents.state import AgentState


async def coach_node(state: AgentState) -> dict[str, Any]:
    """Conduct interactive mock technical interview simulation."""
    dossier = state.get("company_dossier") or {}
    company_name = dossier.get("company_name", "Target Company")
    tech_stack = dossier.get("tech_stack", ["Python", "FastAPI", "PostgreSQL"])
    job = state.get("job_details") or {}
    role_title = job.get("title", "Software Engineer")

    messages = state.get("messages", [])
    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        None,
    )

    history = list(state.get("interview_history", []))

    if not last_user_msg:
        # First turn: Generate opening technical question
        core_tech = tech_stack[0] if tech_stack else "System Design"
        question = (
            f"Welcome to your technical prep session for {role_title} at "
            f"{company_name}! Looking at their architecture, they heavily "
            f"leverage {core_tech}. Could you explain how you design and deploy "
            f"stateful workflows or high-concurrency services using {core_tech}?"
        )
        response_msg = {"role": "assistant", "content": question}
        history.append({"turn": 1, "question": question, "answer": None})
    else:
        # Subsequent turns: Provide technical critique and follow-up question
        critique = (
            "Great answer! You clearly demonstrated architectural awareness. "
            "To strengthen your response for their engineering panel, highlight "
            "failure modes, connection pooling limits, and data consistency."
        )
        follow_up = (
            f"Following up, how would you handle horizontal scaling and "
            f"failover in {company_name}'s stack under peak loads?"
        )
        combined_response = f"{critique}\n\n{follow_up}"
        response_msg = {"role": "assistant", "content": combined_response}
        history.append(
            {
                "turn": len(history) + 1,
                "question": follow_up,
                "last_answer": last_user_msg,
            }
        )

    return {
        "interview_history": history,
        "messages": [response_msg],
        "status": "interview_active",
    }
