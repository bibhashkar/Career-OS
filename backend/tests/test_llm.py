"""Unit tests for the Career-OS LLM provider abstraction."""

from unittest.mock import patch

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.agents.llm import (
    MockChatModel,
    get_llm,
    reset_test_llm,
    set_test_llm,
)


class SampleExtractionSchema(BaseModel):
    """Pydantic model for structured output verification."""

    category: str = "general"
    score: float = 0.0


@pytest.mark.asyncio
async def test_get_llm_fallback_mock() -> None:
    """Verify get_llm yields MockChatModel in absence of live credentials."""
    reset_test_llm()
    with patch("app.agents.llm.settings.GEMINI_API_KEY", None):
        llm = get_llm(default_mock_responses=["Answer A", "Answer B"])
        assert isinstance(llm, MockChatModel)

        msg1 = await llm.ainvoke("Prompt 1")
        assert msg1.content == "Answer A"

        msg2 = await llm.ainvoke("Prompt 2")
        assert msg2.content == "Answer B"

        # Check cyclic repeat on exhausted responses
        msg3 = await llm.ainvoke("Prompt 3")
        assert msg3.content == "Answer B"


@pytest.mark.asyncio
async def test_mock_chat_model_structured_output() -> None:
    """Verify mock structured output parses valid JSON and handles invalid JSON."""
    mock_llm = MockChatModel(
        responses=[
            '{"category": "architecture", "score": 94.5}',
            "non-json plaintext critique",
        ]
    )
    chain = mock_llm.with_structured_output(SampleExtractionSchema)

    # First response parses valid JSON
    result1 = await chain.ainvoke("Critique my solution")
    assert isinstance(result1, SampleExtractionSchema)
    assert result1.category == "architecture"
    assert result1.score == 94.5

    # Second response falls back safely on invalid JSON
    result2 = await chain.ainvoke("Another question")
    assert isinstance(result2, SampleExtractionSchema)
    assert result2.category == "general"
    assert result2.score == 0.0


def test_get_llm_gemini_provider() -> None:
    """Verify get_llm constructs ChatGoogleGenerativeAI when GEMINI_API_KEY is set."""
    reset_test_llm()
    with patch("app.agents.llm.settings.GEMINI_API_KEY", "test_gemini_key"):
        with patch("app.agents.llm.settings.LLM_PROVIDER", "gemini"):
            llm = get_llm(model_name="gemini-2.0-flash", temperature=0.5)
            assert isinstance(llm, ChatGoogleGenerativeAI)
            assert llm.model == "gemini-2.0-flash"
            assert llm.temperature == 0.5


def test_set_and_reset_test_llm() -> None:
    """Verify test override hook takes precedence and can be cleared."""
    custom_mock = MockChatModel(responses=["Override message"])
    set_test_llm(custom_mock)
    try:
        assert get_llm() is custom_mock
    finally:
        reset_test_llm()

    assert get_llm() is not custom_mock
