"""Hunter agent node discovering and ranking relevant job postings."""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.job_search import search_jobs


async def hunter_node(state: AgentState) -> dict[str, Any]:
    """Execute job board search matching user role and visa constraints."""
    job_details = state.get("job_details") or {}
    query = job_details.get("title", "Senior AI Engineer")
    location = job_details.get("location", "Remote")
    visa_req = job_details.get("visa_required", False)

    matched_jobs = await search_jobs(
        query=query,
        location=location,
        visa_sponsorship_required=visa_req,
    )

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
