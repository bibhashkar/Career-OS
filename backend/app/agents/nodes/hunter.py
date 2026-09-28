"""
Hunter agent node discovering and filtering target job listings.

The hunter node acts as the candidate's proactive scout. It queries job search
APIs (such as JSearch) or local hermetic fixtures to find active openings matching
the candidate's target job title, preferred locations, and work authorization
constraints (e.g., visa sponsorship requirements).

Constraint & Selection Strategy:
  - Hard Constraints: Candidates requiring visa sponsorship (H-1B, OPT, etc.)
    must have non-sponsoring listings excluded upfront to avoid wasted effort.
  - Candidate Selection: In the automated pipeline, the highest-relevance listing
    (``matched_jobs[0]``) is selected as the primary target for subsequent intel
    gathering and CV tailoring.
"""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.job_search import search_jobs


async def hunter_node(state: AgentState) -> dict[str, Any]:
    """
    Execute job board search matching user role and visa constraints.

    Reads:
      - ``job_details``: Target query parameters (title, location, visa needs).
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
    query = job_details.get("title", "Senior AI Engineer")
    location = job_details.get("location", "Remote")
    visa_req = job_details.get("visa_required", False)

    # Query external job board or hermetic local fixtures
    matched_jobs = await search_jobs(
        query=query,
        location=location,
        visa_sponsorship_required=visa_req,
    )

    # Select the top matching listing to proceed through the tailoring pipeline
    selected_job = matched_jobs[0] if matched_jobs else {}
    current_job_id = state.get("current_job_id") or selected_job.get("id")

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
