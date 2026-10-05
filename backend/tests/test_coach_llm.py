"""Unit tests for coach_node LLM generation and resilience."""

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.llm import MockChatModel, reset_test_llm, set_test_llm
from app.agents.nodes.coach import coach_node
from app.agents.state import AgentState


class FailingChatModel(BaseChatModel):
    """Simulated failing LLM to verify timeout and network resilience."""

    def _generate(self, *args, **kwargs):  # type: ignore
        raise TimeoutError("Simulated LLM connection timeout")

    @property
    def _llm_type(self) -> str:
        return "failing_test_model"


@pytest.mark.asyncio
async def test_coach_node_invokes_llm_for_turns() -> None:
    """Verify coach_node generates questions and critiques via the LLM provider."""
    mock_llm = MockChatModel(
        responses=[
            "Custom LLM opening: Tell me about your distributed actor systems.",
            (
                "Custom LLM critique: Excellent depth on consensus algorithms.\n\n"
                "Custom LLM follow-up: How do you partition state across nodes?"
            ),
        ]
    )
    set_test_llm(mock_llm)
    try:
        # Turn 1
        state_turn_1: AgentState = {
            "company_dossier": {
                "company_name": "Synthetix AI",
                "tech_stack": ["Rust", "Python"],
            },
            "job_details": {"title": "Distributed Systems Engineer"},
            "messages": [],
            "interview_history": [],
        }
        res_1 = await coach_node(state_turn_1)
        assert len(res_1["interview_history"]) == 1
        assert "distributed actor systems" in res_1["messages"][0]["content"]

        # Turn 2
        state_turn_2: AgentState = {
            **state_turn_1,
            "interview_history": res_1["interview_history"],
            "messages": [
                *res_1["messages"],
                {"role": "user", "content": "I use Raft consensus protocols."},
            ],
        }
        res_2 = await coach_node(state_turn_2)
        assert len(res_2["interview_history"]) == 1  # merge_list will append
        assert "consensus algorithms" in res_2["messages"][0]["content"]
        assert "partition state" in res_2["messages"][0]["content"]
    finally:
        reset_test_llm()


@pytest.mark.asyncio
async def test_coach_node_resilient_fallback_on_failure() -> None:
    """Verify coach_node falls back cleanly if LLM invocation raises an exception."""
    set_test_llm(FailingChatModel())
    try:
        state: AgentState = {
            "company_dossier": {
                "company_name": "Resilient Corp",
                "tech_stack": ["Go", "Kubernetes"],
            },
            "job_details": {"title": "Platform Lead"},
            "messages": [],
            "interview_history": [],
        }
        res = await coach_node(state)
        assert res["status"] == "interview_active"
        assert len(res["interview_history"]) == 1
        assert "Resilient Corp" in res["messages"][0]["content"]
    finally:
        reset_test_llm()
