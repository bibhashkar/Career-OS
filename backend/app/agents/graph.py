"""
LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing.

This module defines the directed acyclic and cyclic workflow graphs that govern
Career-OS agents. It compiles three distinct graph applications:
  1. ``pipeline_app``: Full candidate lifecycle (profiler -> hunter -> intel ->
     tailor -> ats -> [retry if < 75%]).
  2. ``interview_app``: Multi-turn, stateful mock technical interview coaching.
  3. ``reflector_app``: Post-session feedback synthesis and prompt weight tuning.

Why compile separate graphs instead of one monolithic graph?
Decoupling into specialized graphs provides clear execution boundaries. A user
evaluating jobs does not run the interactive interview loop, and an active
WebSocket interview session does not re-trigger job discovery or CV tailoring.
Each graph can also be check-pointed and resumed independently using different
``thread_id`` namespaces.

Loop Guard Architecture:
The ATS evaluation cycle (ats_node -> route_ats -> tailor_node) is inherently
cyclic. Without an explicit loop guard, an intractable job description could
cause an infinite revision loop, consuming unbounded LLM tokens and database I/O.
The ``route_ats`` conditional edge guarantees termination by enforcing two
conditions: score must be below 75.0% AND revision_count must be strictly
less than 3.
"""

import logging
from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from app.agents.nodes.ats import ats_node
from app.agents.nodes.coach import coach_node
from app.agents.nodes.hunter import hunter_node
from app.agents.nodes.intel import intel_node
from app.agents.nodes.profiler import profiler_node
from app.agents.nodes.reflector import reflector_node
from app.agents.nodes.tailor import tailor_node
from app.agents.state import AgentState
from app.core.config import settings

# Default in-memory checkpointer for hermetic test isolation and fast local execution.
# In production, pass an instance of ``PostgresSaver`` to enable persistent,
# distributed checkpoints that survive server restarts.
default_checkpointer = MemorySaver()
_postgres_pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None
_postgres_saver: AsyncPostgresSaver | None = None
logger = logging.getLogger("career_os.agents.graph")


def route_ats(state: AgentState) -> Literal["tailor", "__end__"]:
    """
    Determine whether to route back to tailor_node or terminate the pipeline.

    Routing decisions:
      - Returns ``"tailor"`` if ATS score is below 75.0% AND fewer than 3
        revisions have occurred, instructing LangGraph to run tailor_node again
        with updated keyword guidance.
      - Returns ``"__end__"`` if the score meets or exceeds 75.0% (candidate is
        competitive) OR if the revision limit of 3 has been reached (guarding
        against runaway recursion).

    Args:
        state: Current agent execution state holding ats_score and revision_count.

    Returns:
        The target node name ("tailor") or graph termination ("__end__").
    """
    score = state.get("ats_score", 0.0)
    revisions = state.get("revision_count", 0)

    # Loop guard: bounded limit to max revisions preventing runaway recursion
    if score < settings.ATS_PASS_THRESHOLD and revisions < settings.MAX_REVISIONS:
        return "tailor"
    return "__end__"


def create_pipeline_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """
    Build and compile the end-to-end CV discovery, intelligence, and ATS graph.

    Execution Flow:
      START -> profiler -> hunter -> intel -> tailor -> ats
                 ^                                        |
                 |-------- route_ats (<75% & rev<3) ------|
                                  |
                                  +--> (__end__ if >=75% or rev>=3)

    Args:
        checkpointer: Checkpoint saver for state persistence. Defaults to
                      in-memory ``MemorySaver`` if omitted.

    Returns:
        CompiledStateGraph ready for async invocation via ``.ainvoke()``.
    """
    builder = StateGraph(AgentState)

    # Register workflow nodes
    builder.add_node("profiler", profiler_node)
    builder.add_node("hunter", hunter_node)
    builder.add_node("intel", intel_node)
    builder.add_node("tailor", tailor_node)
    builder.add_node("ats", ats_node)

    # Define linear execution progression
    builder.add_edge(START, "profiler")
    builder.add_edge("profiler", "hunter")
    builder.add_edge("hunter", "intel")
    builder.add_edge("intel", "tailor")
    builder.add_edge("tailor", "ats")

    # Conditional cyclic loop edge: ATS evaluation routing
    builder.add_conditional_edges(
        "ats",
        route_ats,
        {"tailor": "tailor", "__end__": END},
    )

    return builder.compile(checkpointer=checkpointer or MemorySaver())


def create_interview_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """
    Build and compile the stateful mock technical interview coaching graph.

    Each invocation of this graph processes one conversational turn:
      - Reads accumulated messages and company dossier context.
      - Evaluates the candidate's last answer.
      - Generates technical critique and a follow-up question.
      - Checkpoints conversational state under the session's ``thread_id``.

    Args:
        checkpointer: Checkpoint saver enabling pause/resume over WebSockets.

    Returns:
        CompiledStateGraph for multi-turn coaching execution.
    """
    builder = StateGraph(AgentState)
    builder.add_node("coach", coach_node)
    builder.add_edge(START, "coach")
    builder.add_edge("coach", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())


def create_reflector_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """
    Build and compile the feedback synthesis and prompt directive reflection graph.

    Analyzes candidate reviews (e.g. "ask harder questions", "be more concise")
    and adjusts prompt weight parameters (technical_depth, brevity, style)
    for subsequent coaching and CV tailoring sessions.

    Args:
        checkpointer: Checkpoint saver for state persistence.

    Returns:
        CompiledStateGraph for feedback reflection execution.
    """
    builder = StateGraph(AgentState)
    builder.add_node("reflector", reflector_node)
    builder.add_edge(START, "reflector")
    builder.add_edge("reflector", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())


# Pre-compiled application graph instances for global use across API routers.
pipeline_app = create_pipeline_graph()
interview_app = create_interview_graph()
reflector_app = create_reflector_graph()


async def init_postgres_saver(
    conn_string: str | None = None,
) -> AsyncPostgresSaver | None:
    """
    Initialize persistent AsyncPostgresSaver and attach it to graph applications.

    In development/production environments, this creates an AsyncConnectionPool,
    runs saver.setup() to initialize Postgres checkpoint tables, and attaches
    the saver to pipeline_app, interview_app, and reflector_app.

    Args:
        conn_string: Optional libpq connection string. If None, derived from settings.

    Returns:
        The active AsyncPostgresSaver instance if connection succeeds, else None.
    """
    global _postgres_pool, _postgres_saver
    if conn_string is None:
        conn_string = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    try:
        _postgres_pool = AsyncConnectionPool(
            conninfo=conn_string,
            min_size=1,
            max_size=10,
            timeout=2.0,
            open=False,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
                "connect_timeout": 2,
            },
        )
        await _postgres_pool.open(wait=True, timeout=2.0)
        _postgres_saver = AsyncPostgresSaver(_postgres_pool)
        await _postgres_saver.setup()

        # Attach persistent checkpointer to compiled graph applications
        pipeline_app.checkpointer = _postgres_saver
        interview_app.checkpointer = _postgres_saver
        reflector_app.checkpointer = _postgres_saver
        return _postgres_saver
    except Exception as exc:
        logger.warning(
            f"Failed to initialize AsyncPostgresSaver; "
            f"using MemorySaver fallback: {exc}"
        )
        if _postgres_pool:
            try:
                await _postgres_pool.close()
            except Exception as pool_exc:
                logger.debug(
                    f"Error closing PostgreSQL pool on init failure: {pool_exc}"
                )
            _postgres_pool = None
        _postgres_saver = None
        return None


async def close_postgres_saver() -> None:
    """Close the underlying PostgreSQL connection pool on shutdown."""
    global _postgres_pool, _postgres_saver
    if _postgres_pool:
        try:
            await _postgres_pool.close()
        except Exception as exc:
            logger.warning(f"Error closing AsyncPostgresSaver connection pool: {exc}")
        _postgres_pool = None
    _postgres_saver = None
