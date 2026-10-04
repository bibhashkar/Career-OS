"""
Shared state schema and reducers for LangGraph multi-agent workflows.

LangGraph execution is driven by a single state object passed between nodes.
Nodes do not mutate state directly; instead, each node returns a partial
dictionary containing only the keys it wishes to update. LangGraph merges
these partial updates according to each field's reduction semantics.

Why TypedDict with total=False?
In Python's typing system, a standard TypedDict requires all keys to be present
in every dictionary instance. By setting ``total=False``, we declare that nodes
can return partial dictionaries (e.g. ``{"ats_score": 82.0}``) without static
type errors, while still enforcing that any key provided matches its declared
type.

Why explicit merge_list reducers?
By default, LangGraph replaces the previous value of a state key with the new
value returned by a node. For append-only communication channels — such as chat
messages, interview turns, and feedback audit logs — replacement would discard
earlier history. Wrapping these fields in ``Annotated[list[T], merge_list]``
instructs LangGraph to append new list elements to existing ones across node
boundaries and multi-turn WebSocket sessions.
"""

from typing import Annotated, Any, TypedDict


def merge_list(left: list[Any], right: list[Any]) -> list[Any]:
    """
    Append incoming list items to the existing state list.

    Used as a LangGraph reducer for append-only state channels. When a node
    returns ``{"messages": [new_msg]}``, LangGraph invokes this reducer with
    the current list as ``left`` and the node's update as ``right``, preserving
    all previous messages while appending new turns.

    Args:
        left: The existing list accumulated in the current execution thread.
        right: The new elements produced by the most recent node execution.

    Returns:
        A new concatenated list containing all prior and recent items.
    """
    return left + right


class AgentState(TypedDict, total=False):
    """
    Execution state schema shared across all Career-OS LangGraph agent nodes.

    This schema serves as the single source of truth during graph execution.
    Individual agent nodes specialize in reading specific subsets of this state
    and returning updates to other subsets:
      - Profiler reads ``user_id`` and writes initial constraints.
      - Hunter reads constraints and writes ``current_job_id`` / ``job_details``.
      - Intel reads ``job_details`` and writes ``company_dossier``.
      - Tailor reads ``job_details`` and writes ``cv_draft`` / ``matched_cv_blocks``.
      - ATS reads ``cv_draft`` and writes ``ats_score`` / ``ats_feedback``.
      - Coach reads dossier and messages to update ``interview_history``.
      - Reflector reads ``feedback_logs`` and computes weight adjustments.
    """

    # ---- User & Target Context ----
    # Unique identifier of the authenticated candidate profile.
    user_id: str | None
    # Identifier of the job listing currently being targeted or analyzed.
    current_job_id: str | None
    # Parsed job metadata: title, company name, location, ATS requirements.
    job_details: dict[str, Any] | None
    # Researched intelligence: tech stack, business model, recent news.
    company_dossier: dict[str, Any] | None

    # ---- Candidate Constraints & Directives ----
    # Candidate work authorization constraint (True if requiring sponsorship).
    visa_required: bool
    # Stylistic guidelines: e.g. style, brevity, technical_depth, formality.
    tone_directives: dict[str, Any]

    # ---- CV Tailoring & Retrieval ----
    # Achievement chunks retrieved from pgvector by semantic similarity.
    matched_cv_blocks: list[dict[str, Any]]
    # Assembled CV draft formatted for target job requirements.
    cv_draft: dict[str, Any] | None

    # ---- ATS Evaluation & Loop Guards ----
    # Percentage compatibility score (0.0 to 100.0) calculated by ats_node.
    ats_score: float
    # Detailed feedback: matched keywords, missing keywords, recommendations.
    ats_feedback: dict[str, Any] | None
    # Iteration counter incremented by tailor_node to enforce cyclic loop bounds.
    revision_count: int

    # ---- Mock Interview & Reflection State (Append-Only Channels) ----
    # Turn-by-turn history of interview questions, candidate answers, and critique.
    interview_history: Annotated[list[dict[str, Any]], merge_list]
    # Historical user feedback and synthesized prompt weight adjustments.
    feedback_logs: Annotated[list[dict[str, Any]], merge_list]
    # Raw candidate feedback currently being synthesized by reflector_node.
    user_feedback: str | None
    # Conversational messages stream passed to LLMs and WebSocket clients.
    messages: Annotated[list[dict[str, Any]], merge_list]

    # ---- Execution Status ----
    # High-level state lifecycle flag (e.g. "jobs_discovered", "cv_tailored").
    status: str
