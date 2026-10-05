# ADR-005: LLM Provider Abstraction and Google Gemini Integration

## Status
Accepted

## Context
Career-OS requires LLM inference across multiple agent nodes (coach questions and critique, CV tailoring, ATS evaluation, reflection, company tech stack extraction). We need a unified provider abstraction that allows swappable model backends, supports structured JSON outputs, and enables hermetic mock execution in CI without external network access or paid API keys.

## Decision
1. Implement `app/agents/llm.py` providing `get_llm(model_type, temperature)` returning a `BaseChatModel`.
2. Standardize on **Google Gemini** (`ChatGoogleGenerativeAI`, default model `gemini-1.5-flash` or `gemini-1.5-pro`) via `langchain-google-genai` when `settings.GEMINI_API_KEY` is present.
3. Automatically fall back to a hermetic `MockChatModel` when API keys are absent, providing deterministic, schema-compliant outputs for test suites and offline local development.
4. Support structured output generation via `.with_structured_output(PydanticModel)` for deterministic agent parsing.

## Consequences
- **Positive:** Zero external dependencies for test execution; high inference performance and cost efficiency with Google Gemini in production.
- **Negative:** Provider-specific formatting differences must be abstracted via LangChain's common message and tool protocols.
