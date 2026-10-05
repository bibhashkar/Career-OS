"""Unit tests for LangGraph recursion bounds and execution limit guards."""

import pytest
from langgraph.errors import GraphRecursionError

from app.agents.graph import pipeline_app
from app.core.config import settings


def test_settings_defines_graph_recursion_limit() -> None:
    """Verify GRAPH_RECURSION_LIMIT is configured and exceeds single pass length."""
    assert settings.GRAPH_RECURSION_LIMIT >= 15


@pytest.mark.asyncio
async def test_pipeline_graph_enforces_recursion_limit() -> None:
    """Verify that setting a low recursion limit raises GraphRecursionError."""
    initial_state = {
        "user_id": "test-user-recursion",
        "job_details": {
            "title": "Staff AI Engineer",
            "company_name": "NexusAI Labs",
            "ats_requirements": {"required_skills": ["Python"]},
        },
        "revision_count": 0,
    }
    # Setting recursion_limit=2 halts before the 5 pipeline nodes can complete
    with pytest.raises(GraphRecursionError):
        await pipeline_app.ainvoke(
            initial_state,
            config={
                "configurable": {"thread_id": "test_rec_bound"},
                "recursion_limit": 2,
            },
        )
