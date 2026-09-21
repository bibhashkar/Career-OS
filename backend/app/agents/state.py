"""TypedDict state definitions for the LangGraph multi-agent workflow."""

from typing import Annotated, Any, TypedDict


def merge_list(left: list[Any], right: list[Any]) -> list[Any]:
    """Reducer appending incoming items to an existing state list."""
    return left + right


class AgentState(TypedDict, total=False):
    """Execution state schema passed across LangGraph nodes."""

    # User & Target Context
    user_id: str | None
    current_job_id: str | None
    job_details: dict[str, Any] | None
    company_dossier: dict[str, Any] | None

    # CV Tailoring & Retrieval
    matched_cv_blocks: list[dict[str, Any]]
    cv_draft: dict[str, Any] | None

    # ATS Evaluation & Loop Guards
    ats_score: float
    ats_feedback: dict[str, Any] | None
    revision_count: int

    # Mock Interview & Reflection State
    interview_history: Annotated[list[dict[str, Any]], merge_list]
    feedback_logs: Annotated[list[dict[str, Any]], merge_list]
    messages: Annotated[list[dict[str, Any]], merge_list]

    # Execution Status
    status: str
