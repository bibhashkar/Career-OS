"""
LLM provider abstraction and hermetic model factory for Career-OS agents.

Why an abstraction layer?
Career-OS agent nodes (coach, tailor, ats, reflector) need language models for
reasoning, structured evaluation, and text synthesis. Direct instantiation of
vendor-specific client classes inside nodes binds business logic to a single
cloud provider, prevents offline development, and makes unit tests fragile and
dependent on external network availability.

This module provides a unified factory function (``get_llm``) that selects the
configured model provider (defaulting to Google Gemini via
``langchain-google-genai``) when valid API credentials are supplied in the
environment. When running in hermetic test environments or local development
without an API key, the factory gracefully falls back to a deterministic
``MockChatModel`` that satisfies both freeform chat invocation and Pydantic
structured output extraction without hitting external endpoints.
"""

import json
import os
from collections.abc import Sequence
from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

# Global test override hook for unit and integration testing
_test_llm: BaseChatModel | None = None


class MockChatModel(FakeListChatModel):
    """
    Deterministic mock chat model supporting structured outputs and cyclic reuse.

    Standard ``FakeListChatModel`` raises a ``ValueError`` when its static list of
    responses is exhausted, and does not implement ``with_structured_output``.
    This subclass extends it to:
      1. Repeat the final response if more calls occur than initially seeded.
      2. Provide a default simulated response if initialized with an empty list.
      3. Implement ``with_structured_output`` to parse JSON payloads into Pydantic
         models, falling back to schema defaults on non-JSON content.
    """

    def _call(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> str:
        """Return the next simulated response or repeat the terminal entry."""
        if not self.responses:
            return "Simulated deterministic LLM response for Career-OS."
        if self.i >= len(self.responses):
            return self.responses[-1]
        response = self.responses[self.i]
        self.i += 1
        return response

    def with_structured_output(
        self,
        schema: dict[str, Any] | type,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Runnable[Any, Any]:
        """
        Produce a runnable chain that validates simulated JSON into a Pydantic model.

        Args:
            schema: Target Pydantic model class or schema dict for structured output.
            include_raw: Whether to include the raw message with parsed output.
            kwargs: Additional arguments ignored by mock implementation.

        Returns:
            Runnable yielding an instance of ``schema`` or a schema dictionary.
        """

        async def _extract(input_val: Any) -> Any:
            msg = await self.ainvoke(input_val)
            raw_text = (
                msg.content if isinstance(msg.content, str) else str(msg.content or "")
            )
            parsed: Any = None
            try:
                data = json.loads(raw_text)
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    parsed = (
                        schema.model_validate(data)
                        if isinstance(data, dict)
                        else schema.model_construct()
                    )
                else:
                    parsed = data
            except Exception:
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    parsed = schema.model_construct()
                else:
                    parsed = {}

            if include_raw:
                return {"raw": msg, "parsed": parsed, "parsing_error": None}
            return parsed

        return RunnableLambda(_extract)


def set_test_llm(model: BaseChatModel | None) -> None:
    """
    Override the model instance returned by ``get_llm`` for testing.

    Args:
        model: Custom chat model instance, or None to reset.
    """
    global _test_llm
    _test_llm = model


def reset_test_llm() -> None:
    """Clear any active test LLM override, restoring default resolution."""
    global _test_llm
    _test_llm = None


def get_llm(
    model_name: str | None = None,
    temperature: float = 0.2,
    default_mock_responses: Sequence[str] | None = None,
    force_real: bool = False,
) -> BaseChatModel:
    """
    Resolve and return a configured BaseChatModel instance.

    Selection Priority:
      1. Explicit test override (if configured via ``set_test_llm``).
      2. Hermetic ``MockChatModel`` when running under pytest or in test mode,
         unless ``force_real=True`` is explicitly specified.
      3. Google Gemini (``ChatGoogleGenerativeAI``) when ``LLM_PROVIDER == 'gemini'``
         and ``GEMINI_API_KEY`` is populated.
      4. Fallback ``MockChatModel`` for offline CI testing and local environments
         without active cloud API credentials.

    Args:
        model_name: Optional override for the underlying model identifier.
        temperature: Sampling temperature for generation randomness (0.0 - 1.0).
        default_mock_responses: Optional predetermined response strings for mock.
        force_real: When True, bypasses test isolation to construct real client.

    Returns:
        Configured BaseChatModel instance.
    """
    if _test_llm is not None:
        return _test_llm

    responses = (
        list(default_mock_responses)
        if default_mock_responses
        else ["Default hermetic response from Career-OS intelligence provider."]
    )

    is_testing = "PYTEST_CURRENT_TEST" in os.environ or settings.APP_ENV == "test"
    if is_testing and not force_real:
        return MockChatModel(responses=responses)

    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        target_model = model_name or settings.GEMINI_MODEL
        return ChatGoogleGenerativeAI(
            model=target_model,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )

    return MockChatModel(responses=responses)
