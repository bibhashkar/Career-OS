"""Unit tests for tailor_node LLM synthesis and fallback behavior."""

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.llm import MockChatModel, reset_test_llm, set_test_llm
from app.agents.nodes.tailor import tailor_node
from app.agents.state import AgentState


class FailingChatModel(BaseChatModel):
    """Simulated failing LLM to verify resilience on error/timeout."""

    def _generate(self, *args, **kwargs):  # type: ignore
        raise TimeoutError("Simulated LLM connection timeout")

    @property
    def _llm_type(self) -> str:
        return "failing_test_model"


@pytest.mark.asyncio
async def test_tailor_node_synthesizes_summary_via_llm() -> None:
    """Verify tailor_node sets cv_draft professional_summary from the LLM provider."""
    mock_llm = MockChatModel(
        responses=[
            (
                "Staff Distributed Systems Architect with extensive experience in "
                "fault-tolerant streaming pipelines at massive scale."
            )
        ]
    )
    set_test_llm(mock_llm)
    try:
        state: AgentState = {
            "job_details": {
                "title": "Principal Distributed Systems Engineer",
                "company_name": "CloudScale AI",
                "ats_requirements": {"required_skills": ["Python", "FastAPI"]},
            },
            "revision_count": 0,
        }
        res = await tailor_node(state)
        assert res["status"] == "cv_tailored"
        assert (
            "fault-tolerant streaming pipelines"
            in res["cv_draft"]["professional_summary"]
        )
        assert res["cv_draft"]["revision_version"] == 1
    finally:
        reset_test_llm()


@pytest.mark.asyncio
async def test_tailor_node_falls_back_on_llm_failure() -> None:
    """Verify tailor_node provides robust fallback summary when LLM fails."""
    set_test_llm(FailingChatModel())
    try:
        state: AgentState = {
            "job_details": {
                "title": "AI Backend Engineer",
                "company_name": "Robust Solutions",
                "ats_requirements": {"required_skills": ["Python"]},
            },
            "revision_count": 1,
        }
        res = await tailor_node(state)
        assert res["status"] == "cv_tailored"
        assert "proven mastery" in res["cv_draft"]["professional_summary"]
        assert res["cv_draft"]["revision_version"] == 2
    finally:
        reset_test_llm()
