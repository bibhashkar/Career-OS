"""Unit tests for LangGraph checkpointer initialization and lifecycle."""

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import (
    close_postgres_saver,
    init_postgres_saver,
    interview_app,
    pipeline_app,
    reflector_app,
)
from app.agents.state import AgentState


@pytest.mark.asyncio
async def test_init_postgres_saver_handles_unreachable_db() -> None:
    """Verify init_postgres_saver gracefully falls back when database is offline."""
    # Attempt connecting to an unreachable port with 1-second timeout
    unreachable_conn = (
        "postgresql://user:pass@127.0.0.1:59999/nonexistent?connect_timeout=1"
    )
    saver = await init_postgres_saver(unreachable_conn)

    # Must return None and not raise an unhandled exception
    assert saver is None

    # Graph apps must still possess a valid checkpointer (MemorySaver)
    assert pipeline_app.checkpointer is not None
    assert interview_app.checkpointer is not None
    assert reflector_app.checkpointer is not None


@pytest.mark.asyncio
async def test_close_postgres_saver_is_idempotent() -> None:
    """Verify closing postgres saver multiple times does not raise errors."""
    await close_postgres_saver()
    await close_postgres_saver()


@pytest.mark.asyncio
async def test_graph_checkpointer_swap_preserves_execution() -> None:
    """Verify swapping checkpointer preserves state retrieval in graph execution."""
    custom_saver = MemorySaver()
    original_saver = interview_app.checkpointer

    try:
        interview_app.checkpointer = custom_saver
        config: RunnableConfig = {
            "configurable": {"thread_id": "thread_checkpointer_swap_01"}
        }

        state: AgentState = {
            "company_dossier": {"company_name": "Checkpointer Inc"},
            "messages": [],
        }
        res = await interview_app.ainvoke(state, config=config)
        assert len(res["interview_history"]) == 1

        # Check state exists in custom_saver
        saved_state = await interview_app.aget_state(config)
        assert saved_state is not None
        assert len(saved_state.values.get("interview_history", [])) == 1
    finally:
        interview_app.checkpointer = original_saver
