"""
Coach agent node managing stateful, interactive mock technical interviews.

The coach node simulates a senior technical interviewer tailored to the candidate's
target employer. Rather than asking generic interview questions, it grounds its
questions in the company's actual technical stack (from ``company_dossier``) and
the specific responsibilities of the role (from ``job_details``).

Multi-Turn Conversational Architecture:
  - Turn 1 (Opening): When invoked with an empty message history, the coach
    welcomes the candidate and asks an architectural question focused on the
    company's core technology.
  - Turn >= 2 (Follow-ups): When candidate messages are present, the coach
    critiques the previous answer (highlighting production concerns like failure
    modes, pooling, and concurrency) and asks an escalating follow-up question.
  - Statefulness: Each turn appends to ``interview_history`` and ``messages`` via
    the ``merge_list`` reducer, enabling pause and resume across WebSocket sessions.
"""

from typing import Any

from app.agents.state import AgentState


async def coach_node(state: AgentState) -> dict[str, Any]:
    """
    Process one conversational turn in the interactive mock interview.

    Reads:
      - ``company_dossier``: Researched tech stack and company profile.
      - ``job_details``: Target role title and requirements.
      - ``messages``: Message history to locate the most recent candidate reply.
      - ``interview_history``: Turn counter and previous Q&A pairs.

    Writes:
      - ``interview_history``: Appends the new turn record.
      - ``messages``: Appends the coach's question or feedback.
      - ``status``: Set to ``"interview_active"``.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update containing the new interview turn and assistant message.
    """
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
        # First turn: Generate personalized opening question using researched stack
        core_tech = tech_stack[0] if tech_stack else "System Design"
        question = (
            f"Welcome to your technical prep session for {role_title} at "
            f"{company_name}! Looking at their architecture, they heavily "
            f"leverage {core_tech}. Could you explain how you design and deploy "
            f"stateful workflows or high-concurrency services using {core_tech}?"
        )
        response_msg = {"role": "assistant", "content": question}
        new_turn = {"turn": 1, "question": question, "answer": None}
    else:
        # Subsequent turns: Provide technical critique and deeper follow-up
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
        new_turn = {
            "turn": len(history) + 1,
            "question": follow_up,
            "last_answer": last_user_msg,
        }

    return {
        "interview_history": [new_turn],
        "messages": [response_msg],
        "status": "interview_active",
    }
