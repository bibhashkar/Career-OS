"""Unit tests for reflector_node structured LLM output and resilience."""

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.llm import MockChatModel, reset_test_llm, set_test_llm
from app.agents.nodes.reflector import reflector_node
from app.agents.state import AgentState


class FailingChatModel(BaseChatModel):
    """Simulated failing LLM to verify resilience on error."""

    def _generate(self, *args, **kwargs):  # type: ignore
        raise TimeoutError("Simulated LLM connection timeout")

    @property
    def _llm_type(self) -> str:
        return "failing_test_model"


@pytest.mark.asyncio
async def test_reflector_node_derives_structured_weights() -> None:
    """Verify reflector_node extracts prompt adjustments from structured LLM."""
    mock_llm = MockChatModel(
        responses=[
            '{"technical_depth": 0.98, "brevity": 0.88, "style": "rigorous", '
            '"rationale": "Candidate requested deep database internals."}'
        ]
    )
    set_test_llm(mock_llm)
    try:
        state: AgentState = {
            "feedback_logs": [
                {
                    "thread_id": "thread_custom_101",
                    "user_feedback": "Dive deeper into Raft and Paxos internals.",
                }
            ]
        }
        res = await reflector_node(state)
        assert res["status"] == "feedback_reflected"
        adjustments = res["feedback_logs"][-1]["prompt_weight_adjustments"]
        assert adjustments["technical_depth"] == 0.98
        assert adjustments["brevity"] == 0.88
        assert adjustments["style"] == "rigorous"
    finally:
        reset_test_llm()


@pytest.mark.asyncio
async def test_reflector_node_falls_back_on_failure() -> None:
    """Verify reflector_node gracefully falls back to heuristic when LLM fails."""
    set_test_llm(FailingChatModel())
    try:
        state: AgentState = {
            "feedback_logs": [
                {
                    "thread_id": "thread_fallback_102",
                    "user_feedback": "Please keep things more concise.",
                }
            ]
        }
        res = await reflector_node(state)
        assert res["status"] == "feedback_reflected"
        adjustments = res["feedback_logs"][-1]["prompt_weight_adjustments"]
        assert adjustments["brevity"] == 0.95
    finally:
        reset_test_llm()
