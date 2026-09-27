"""LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing."""

from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.nodes.ats import ats_node
from app.agents.nodes.coach import coach_node
from app.agents.nodes.hunter import hunter_node
from app.agents.nodes.intel import intel_node
from app.agents.nodes.profiler import profiler_node
from app.agents.nodes.reflector import reflector_node
from app.agents.nodes.tailor import tailor_node
from app.agents.state import AgentState

# Default in-memory checkpointer for hermetic test isolation and fast fallback
default_checkpointer = MemorySaver()


def route_ats(state: AgentState) -> Literal["tailor", "__end__"]:
    """Conditionally route back to tailor_node if ATS score < 75%."""
    score = state.get("ats_score", 0.0)
    revisions = state.get("revision_count", 0)

    # Loop guard: bounded limit to max 3 revisions to prevent runaway recursion
    if score < 75.0 and revisions < 3:
        return "tailor"
    return "__end__"


def create_pipeline_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Build the end-to-end CV discovery, intelligence, tailoring, and ATS graph."""
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

    return builder.compile(checkpointer=checkpointer or default_checkpointer)


def create_interview_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Build the stateful mock interview coaching graph keyed on thread_id."""
    builder = StateGraph(AgentState)
    builder.add_node("coach", coach_node)
    builder.add_edge(START, "coach")
    builder.add_edge("coach", END)
    return builder.compile(checkpointer=checkpointer or default_checkpointer)


def create_reflector_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Build the feedback synthesis and prompt directive reflection graph."""
    builder = StateGraph(AgentState)
    builder.add_node("reflector", reflector_node)
    builder.add_edge(START, "reflector")
    builder.add_edge("reflector", END)
    return builder.compile(checkpointer=checkpointer or default_checkpointer)


# Pre-compiled application graph instances
pipeline_app = create_pipeline_graph()
interview_app = create_interview_graph()
reflector_app = create_reflector_graph()
