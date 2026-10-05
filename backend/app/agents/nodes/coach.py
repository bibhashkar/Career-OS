"""
Coach agent node managing stateful, interactive mock technical interviews.

The coach node simulates a senior technical interviewer tailored to the candidate's
target employer. Rather than asking generic interview questions, it grounds its
questions in the company's actual technical stack (from ``company_dossier``) and
the specific responsibilities of the role (from ``job_details``).

Multi-Turn Conversational Architecture:
  - Turn 1 (Opening): When invoked with an empty message history, the coach
    synthesizes a personalized architectural question focused on the company's
    core technology using Google Gemini via ``get_llm``.
  - Turn >= 2 (Follow-ups): When candidate messages are present, the coach
    critiques the previous answer (highlighting production concerns like failure
    modes, pooling, and concurrency) and asks an escalating follow-up question.
  - Statefulness: Each turn appends to ``interview_history`` and ``messages`` via
    the ``merge_list`` reducer, enabling pause and resume across WebSocket sessions.
  - Resilient Fallback: If external LLM calls time out or encounter rate limits,
    deterministic fallbacks ensure seamless session continuity without crashing.
"""

import asyncio
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

logger = logging.getLogger("career_os.nodes.coach")


async def coach_node(state: AgentState) -> dict[str, Any]:
    """
    Process one conversational turn in the interactive mock interview.

    Reads:
      - ``company_dossier``: Researched tech stack and company profile.
      - ``job_details``: Target role title and requirements.
      - ``messages``: Message history to locate the most recent candidate reply.
      - ``interview_history``: Turn counter and previous Q&A pairs.
      - ``tone_directives``: Adaptive interview tone derived from feedback logs.

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
    tech_stack = dossier.get("tech_stack") or ["Python", "FastAPI", "PostgreSQL"]
    job = state.get("job_details") or {}
    role_title = job.get("title", "Software Engineer")
    tone = state.get("tone_directives") or "rigorous, constructive, and concise"

    messages = state.get("messages", [])
    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        None,
    )

    history = list(state.get("interview_history", []))
    core_tech = tech_stack[0] if tech_stack else "System Design"

    # Deterministic fallback responses for offline tests and network resiliency
    fallback_opening = (
        f"Welcome to your technical prep session for {role_title} at "
        f"{company_name}! Looking at their architecture, they heavily "
        f"leverage {core_tech}. Could you explain how you design and deploy "
        f"stateful workflows or high-concurrency services using {core_tech}?"
    )
    fallback_critique = (
        "Great answer! You clearly demonstrated architectural awareness. "
        "To strengthen your response for their engineering panel, highlight "
        "failure modes, connection pooling limits, and data consistency."
    )
    fallback_follow_up = (
        f"Following up, how would you handle horizontal scaling and "
        f"failover in {company_name}'s stack under peak loads?"
    )
    fallback_subsequent = f"{fallback_critique}\n\n{fallback_follow_up}"

    target_mock_fallback = fallback_subsequent if last_user_msg else fallback_opening
    llm = get_llm(
        temperature=0.3,
        default_mock_responses=[target_mock_fallback],
    )

    system_prompt = (
        f"You are a staff engineer conducting a technical interview for "
        f"{role_title} at {company_name}.\n"
        f"Tech stack: {', '.join(tech_stack)}.\n"
        f"Culture: {dossier.get('culture_notes', 'Reliability and DX')}.\n"
        f"Tone directives: {tone}."
    )

    if not last_user_msg:
        # Turn 1: Opening technical challenge grounded in employer stack
        prompt = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    f"Welcome the candidate to their technical prep session for "
                    f"{role_title} at {company_name}. Inquire about practical "
                    f"system design and tradeoffs using {core_tech}."
                )
            ),
        ]
        try:
            res = await asyncio.wait_for(llm.ainvoke(prompt), timeout=15.0)
            content = (
                res.content if isinstance(res.content, str) else str(res.content)
            ).strip()
            if not content:
                content = fallback_opening
        except Exception as exc:
            logger.debug(f"LLM interview coach opening question fallback: {exc}")
            content = fallback_opening

        response_msg = {"role": "assistant", "content": content}
        new_turn = {"turn": 1, "question": content, "answer": None}
    else:
        # Subsequent turns: Technical critique of answer + deeper follow-up
        prev_q = history[-1].get("question", "previous question") if history else ""
        prompt = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    f"Previous Question: {prev_q}\n"
                    f"Candidate Response: {last_user_msg}\n\n"
                    f"Critique their technical answer highlighting concrete production "
                    f"tradeoffs. Then ask a follow-up question on horizontal scaling "
                    f"and failover in {company_name}'s stack."
                )
            ),
        ]
        try:
            res = await asyncio.wait_for(llm.ainvoke(prompt), timeout=15.0)
            content = (
                res.content if isinstance(res.content, str) else str(res.content)
            ).strip()
            if not content:
                content = fallback_subsequent
        except Exception as exc:
            logger.debug(f"LLM interview coach critique fallback: {exc}")
            content = fallback_subsequent

        response_msg = {"role": "assistant", "content": content}
        new_turn = {
            "turn": len(history) + 1,
            "question": content,
            "last_answer": last_user_msg,
        }

    return {
        "interview_history": [new_turn],
        "messages": [response_msg],
        "status": "interview_active",
    }
