"""Unit tests for company intel LLM tech stack extraction and resilience."""

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.llm import MockChatModel, reset_test_llm, set_test_llm
from app.agents.tools.company_intel import fetch_company_intel


class FailingChatModel(BaseChatModel):
    """Simulated failing LLM to verify resilience on error."""

    def _generate(self, *args, **kwargs):  # type: ignore
        raise TimeoutError("Simulated LLM connection timeout")

    @property
    def _llm_type(self) -> str:
        return "failing_test_model"


@pytest.mark.asyncio
async def test_fetch_company_intel_extracts_via_llm() -> None:
    """Verify unknown company tech stack is extracted via LLM structured output."""
    mock_llm = MockChatModel(
        responses=[
            '{"industry": "High-Frequency Trading", '
            '"tech_stack": ["Rust", "Tokio", "gRPC", "RocksDB"], '
            '"business_model": "Algorithmic market making", '
            '"culture_notes": "Extreme performance and microsecond latency."}'
        ]
    )
    set_test_llm(mock_llm)
    try:
        dossier = await fetch_company_intel("Hyperion Algorithmic Systems")
        assert dossier["company_name"] == "Hyperion Algorithmic Systems"
        assert dossier["industry"] == "High-Frequency Trading"
        assert "Rust" in dossier["tech_stack"]
        assert "Tokio" in dossier["tech_stack"]
        assert dossier["business_model"] == "Algorithmic market making"
    finally:
        reset_test_llm()


@pytest.mark.asyncio
async def test_fetch_company_intel_fallback_resilience() -> None:
    """Verify fallback returns valid profile when LLM call fails."""
    set_test_llm(FailingChatModel())
    try:
        dossier = await fetch_company_intel("Uncharted Technologies")
        assert dossier["company_name"] == "Uncharted Technologies"
        assert "tech_stack" in dossier
        assert isinstance(dossier["tech_stack"], list)
        assert dossier.get("data_origin") == "inferred"
    finally:
        reset_test_llm()
