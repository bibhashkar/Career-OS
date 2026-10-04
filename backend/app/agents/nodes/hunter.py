"""
Hunter agent node discovering and filtering target job listings.

The hunter node acts as the candidate's proactive scout. It queries job search
APIs (such as JSearch) or local hermetic fixtures to find active openings matching
the candidate's target job title, preferred locations, and work authorization
constraints (e.g., visa sponsorship requirements).

Constraint & Selection Strategy:
  - Caller Precedence: If the execution state already specifies an explicit target
    job (via ``current_job_id`` or pre-populated ``job_details`` with company
    and ATS criteria), Hunter preserves that target rather than overwriting it
    with arbitrary search results.
  - Targeted Lookup: If a ``current_job_id`` is requested without full details,
    Hunter locates the corresponding listing from matching results.
  - Hard Constraints: Candidates requiring visa sponsorship (H-1B, OPT, etc.)
    have non-sponsoring listings excluded upfront when searching.
"""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.job_search import search_jobs


async def hunter_node(state: AgentState) -> dict[str, Any]:
    """
    Execute job board search matching user role and visa constraints.

    Reads:
      - ``job_details``: Target query parameters or pre-populated job criteria.
      - ``current_job_id``: Existing job ID if user manually specified a target.

    Writes:
      - ``current_job_id``: Populated with selected job identifier.
      - ``job_details``: Detailed listing attributes (skills, salary, description).
      - ``status``: Set to ``"jobs_discovered"``.
      - ``messages``: System log documenting discovery count and chosen target.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update with discovered job details and system log message.
    """
    job_details = state.get("job_details") or {}
    target_job_id = state.get("current_job_id") or job_details.get("id")

    # If caller already supplied complete target job details, preserve them
    has_company = bool(job_details.get("company_name"))
    has_requirements = bool(job_details.get("ats_requirements"))
    if has_company and (has_requirements or target_job_id):
        selected_job = dict(job_details)
        resolved_job_id = target_job_id or selected_job.get("id")
        if resolved_job_id and not selected_job.get("id"):
            selected_job["id"] = resolved_job_id
        return {
            "current_job_id": resolved_job_id,
            "job_details": selected_job,
            "status": "jobs_discovered",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Hunter preserved target job: "
                        f"'{selected_job.get('title', 'Target Role')}' at "
                        f"'{selected_job.get('company_name')}'."
                    ),
                }
            ],
        }

    query = job_details.get("title", "Senior AI Engineer")
    location = job_details.get("location", "Remote")
    visa_req = state.get("visa_required", job_details.get("visa_required", False))

    # Query external job board or hermetic local fixtures
    matched_jobs = await search_jobs(
        query=query,
        location=location,
        visa_sponsorship_required=visa_req,
    )

    # If a specific job ID was targeted, locate it; otherwise pick top match
    selected_job = {}
    if target_job_id:
        selected_job = next(
            (j for j in matched_jobs if j.get("id") == target_job_id),
            {},
        )
    if not selected_job and matched_jobs:
        selected_job = matched_jobs[0]

    current_job_id = target_job_id or selected_job.get("id")

    return {
        "current_job_id": current_job_id,
        "job_details": selected_job,
        "status": "jobs_discovered",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Hunter discovered {len(matched_jobs)} matching job(s). "
                    f"Selected target: '{selected_job.get('title')}' at "
                    f"'{selected_job.get('company_name')}'."
                ),
            }
        ],
    }
