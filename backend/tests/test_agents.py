"""Unit and integration tests for LangGraph agent workflows and loop guards."""

import pytest

from app.agents.graph import (
    interview_app,
    pipeline_app,
    reflector_app,
    route_ats,
)
from app.agents.nodes.ats import ats_node
from app.agents.nodes.hunter import hunter_node
from app.agents.nodes.tailor import tailor_node
from app.agents.state import AgentState


def test_route_ats_loop_guard() -> None:
    """Verify ATS router enforces cyclic retry and maximum revision limit."""
    # Score below threshold and revisions < 3 should route back to tailor
    state_retry: AgentState = {"ats_score": 68.0, "revision_count": 1}
    assert route_ats(state_retry) == "tailor"

    # Score below threshold but revisions reached 3 should terminate
    state_max_rev: AgentState = {"ats_score": 68.0, "revision_count": 3}
    assert route_ats(state_max_rev) == "__end__"

    # Score >= 75.0 should pass and terminate
    state_pass: AgentState = {"ats_score": 82.5, "revision_count": 1}
    assert route_ats(state_pass) == "__end__"


@pytest.mark.asyncio
async def test_pipeline_graph_end_to_end() -> None:
    """Verify full pipeline through profiler, hunter, intel, tailor, and ats."""
    initial_state: AgentState = {
        "user_id": "user-test-123",
        "job_details": {
            "title": "Senior AI Systems Engineer",
            "company_name": "NexusAI Labs",
            "location": "Remote",
            "ats_requirements": {"required_skills": ["Python", "FastAPI", "LangGraph"]},
        },
    }

    config = {"configurable": {"thread_id": "thread_test_pipeline_001"}}
    final_state = await pipeline_app.ainvoke(initial_state, config=config)

    assert final_state["status"] == "ats_evaluated"
    assert final_state["ats_score"] >= 70.0
    assert final_state["cv_draft"] is not None
    assert final_state["company_dossier"] is not None
    assert final_state["revision_count"] >= 1


@pytest.mark.asyncio
async def test_interview_coach_stateful_turns() -> None:
    """Verify coach graph advances multi-turn technical interview state."""
    thread_id = "thread_mock_interview_999"
    config = {"configurable": {"thread_id": thread_id}}

    # Turn 1: Initial invocation without user message
    turn_1_state: AgentState = {
        "company_dossier": {
            "company_name": "NexusAI Labs",
            "tech_stack": ["Python", "LangGraph"],
        },
        "job_details": {"title": "Staff AI Engineer"},
        "messages": [],
    }
    result_1 = await interview_app.ainvoke(turn_1_state, config=config)
    assert len(result_1["interview_history"]) == 1
    assert "NexusAI Labs" in result_1["messages"][-1]["content"]

    # Turn 2: Candidate sends response
    turn_2_state: AgentState = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "I designed stateful agent pipelines using LangGraph "
                    "persisting to PostgreSQL, handling 1k req/sec."
                ),
            }
        ]
    }
    result_2 = await interview_app.ainvoke(turn_2_state, config=config)
    assert len(result_2["interview_history"]) == 2
    assert "architectural awareness" in result_2["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_reflector_agent_updates_weights() -> None:
    """Verify reflector graph analyzes feedback and updates prompt weights."""
    feedback_state: AgentState = {
        "feedback_logs": [
            {"user_feedback": "Please ask more technical system design questions."}
        ]
    }

    config = {"configurable": {"thread_id": "thread_reflector_001"}}
    result = await reflector_app.ainvoke(feedback_state, config=config)

    assert result["status"] == "feedback_reflected"
    last_log = result["feedback_logs"][-1]
    assert last_log["prompt_weight_adjustments"]["technical_depth"] == 0.95


@pytest.mark.asyncio
async def test_hunter_preserves_caller_job_details() -> None:
    """Verify hunter_node retains caller-provided target job and ID."""
    # Arrange
    target_job = {
        "id": "job-ai-003",
        "title": "Full-Stack AI Application Developer",
        "company_name": "CareerCloud Systems",
        "ats_requirements": {"required_skills": ["React", "FastAPI"]},
    }
    state: AgentState = {
        "current_job_id": "job-ai-003",
        "job_details": target_job,
    }

    # Act
    result = await hunter_node(state)

    # Assert
    assert result["current_job_id"] == "job-ai-003"
    assert result["job_details"]["company_name"] == "CareerCloud Systems"
    assert result["job_details"]["id"] == "job-ai-003"


@pytest.mark.asyncio
async def test_pipeline_preserves_target_job_end_to_end() -> None:
    """Verify pipeline crafts CV and dossier for the requested job, not default."""
    # Arrange
    initial_state: AgentState = {
        "user_id": "user-custom-456",
        "current_job_id": "job-ai-003",
        "job_details": {
            "id": "job-ai-003",
            "title": "Full-Stack AI Application Developer",
            "company_name": "CareerCloud Systems",
            "ats_requirements": {"required_skills": ["React", "FastAPI"]},
        },
    }
    config = {"configurable": {"thread_id": "thread_preserve_target_001"}}

    # Act
    final_state = await pipeline_app.ainvoke(initial_state, config=config)

    # Assert
    assert final_state["current_job_id"] == "job-ai-003"
    assert final_state["cv_draft"]["target_company"] == "CareerCloud Systems"
    assert final_state["company_dossier"]["company_name"] == "CareerCloud Systems"


@pytest.mark.asyncio
async def test_tailor_highlights_only_candidate_proven_skills() -> None:
    """Verify tailor_node never fabricates unproven skills in CV draft."""
    # Arrange
    state: AgentState = {
        "job_details": {
            "title": "Mainframe Specialist",
            "company_name": "LegacyBank",
            "ats_requirements": {"required_skills": ["COBOL", "JCL", "DB2"]},
        },
        "revision_count": 0,
    }

    # Act
    result = await tailor_node(state)
    highlighted = result["cv_draft"]["skills_highlighted"]

    # Assert: none of the unproven required skills should be claimed
    assert "COBOL" not in highlighted
    assert "JCL" not in highlighted
    assert "DB2" not in highlighted
    # Candidate's real skills from default blocks should be present instead
    assert len(highlighted) > 0


@pytest.mark.asyncio
async def test_unmatched_job_enforces_loop_guard_and_fails_ats() -> None:
    """Verify missing qualifications trigger loop guard and conclude with fail score."""
    # Arrange: candidate has no COBOL or JCL in default blocks
    initial_state: AgentState = {
        "user_id": "user-unqualified-789",
        "current_job_id": "job-cobol-999",
        "job_details": {
            "id": "job-cobol-999",
            "title": "COBOL Mainframe Engineer",
            "company_name": "LegacyBank",
            "ats_requirements": {"required_skills": ["COBOL", "JCL", "DB2"]},
        },
    }
    config = {"configurable": {"thread_id": "thread_loop_guard_test_001"}}

    # Act
    final_state = await pipeline_app.ainvoke(initial_state, config=config)

    # Assert: loop guard must cap revisions at 3, score must be below 75
    assert final_state["revision_count"] == 3
    assert final_state["ats_score"] < 75.0
    assert set(final_state["ats_feedback"]["missing_keywords"]) == {
        "COBOL",
        "JCL",
        "DB2",
    }
    assert route_ats(final_state) == "__end__"


@pytest.mark.asyncio
async def test_ats_node_keyword_scoring_diagnostics() -> None:
    """Verify ats_node accurately identifies missing keywords and computes scores."""
    # Arrange
    state: AgentState = {
        "cv_draft": {
            "skills_highlighted": ["Python", "FastAPI"],
        },
        "job_details": {
            "ats_requirements": {
                "required_skills": ["Python", "FastAPI", "Kubernetes", "gRPC"],
            }
        },
        "revision_count": 1,
    }

    # Act
    result = await ats_node(state)

    # Assert
    assert result["ats_feedback"]["matched_keywords"] == ["Python", "FastAPI"]
    assert result["ats_feedback"]["missing_keywords"] == ["Kubernetes", "gRPC"]
    assert result["ats_score"] == 50.0  # 2/4 = 50% * 70 = 35 + 15 baseline = 50.0
    assert result["status"] == "ats_evaluated"
