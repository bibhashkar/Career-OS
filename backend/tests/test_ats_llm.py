"""Unit tests for ATS node LLM structured evaluation and threshold routing."""

from unittest.mock import patch

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.graph import route_ats
from app.agents.llm import MockChatModel, reset_test_llm, set_test_llm
from app.agents.nodes.ats import ats_node
from app.agents.state import AgentState
from app.core.config import settings


class FailingChatModel(BaseChatModel):
    """Simulated failing LLM to verify resilience on error."""

    def _generate(self, *args, **kwargs):  # type: ignore
        raise TimeoutError("Simulated LLM connection timeout")

    @property
    def _llm_type(self) -> str:
        return "failing_test_model"


@pytest.mark.asyncio
async def test_ats_node_evaluates_with_structured_output() -> None:
    """Verify ats_node extracts score and recommendation from LLM structured output."""
    mock_llm = MockChatModel(
        responses=[
            '{"keyword_match_score": 88.5, "formatting_score": 95.0, '
            '"recommendation": "Strong alignment with Kubernetes architecture."}'
        ]
    )
    set_test_llm(mock_llm)
    try:
        state: AgentState = {
            "cv_draft": {
                "skills_highlighted": ["Python", "FastAPI"],
                "professional_summary": "Experienced Python architect.",
            },
            "job_details": {
                "title": "Platform Engineer",
                "ats_requirements": {"required_skills": ["Python", "FastAPI"]},
            },
            "revision_count": 1,
        }
        res = await ats_node(state)
        assert res["status"] == "ats_evaluated"
        assert res["ats_score"] == 88.5
        assert "Kubernetes architecture" in res["ats_feedback"]["recommendation"]
    finally:
        reset_test_llm()


@pytest.mark.asyncio
async def test_ats_node_fallback_resilience() -> None:
    """Verify ats_node falls back to formula scoring when LLM fails."""
    set_test_llm(FailingChatModel())
    try:
        state: AgentState = {
            "cv_draft": {
                "skills_highlighted": ["Python"],
                "professional_summary": "Python dev.",
            },
            "job_details": {
                "title": "Backend Dev",
                "ats_requirements": {"required_skills": ["Python", "Go"]},
            },
            "revision_count": 1,
        }
        res = await ats_node(state)
        assert res["status"] == "ats_evaluated"
        assert isinstance(res["ats_score"], float)
        assert (
            "Incorporate missing critical keywords"
            in (res["ats_feedback"]["recommendation"])
        )
    finally:
        reset_test_llm()


def test_route_ats_respects_settings_thresholds() -> None:
    """Verify route_ats conditions are governed by settings configuration."""
    with patch.object(settings, "ATS_PASS_THRESHOLD", 80.0):
        with patch.object(settings, "MAX_REVISIONS", 2):
            # Score 78% is below threshold 80% with 1 revision -> routes to tailor
            state_retry: AgentState = {"ats_score": 78.0, "revision_count": 1}
            assert route_ats(state_retry) == "tailor"

            # Revision 2 reached max revisions -> terminates
            state_max_rev: AgentState = {"ats_score": 78.0, "revision_count": 2}
            assert route_ats(state_max_rev) == "__end__"

            # Score 82% passes -> terminates
            state_pass: AgentState = {"ats_score": 82.0, "revision_count": 1}
            assert route_ats(state_pass) == "__end__"
