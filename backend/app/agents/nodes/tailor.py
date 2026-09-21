"""Tailor agent node querying pgvector and assembling tailored CV drafts."""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.vector_search import search_cv_blocks


async def tailor_node(state: AgentState) -> dict[str, Any]:
    """Retrieve CV blocks from pgvector and assemble tailored CV draft."""
    user_id = state.get("user_id")
    job = state.get("job_details") or {}
    reqs = job.get("ats_requirements", {})
    required_skills = reqs.get("required_skills", ["Python", "FastAPI"])

    # If revising due to ATS feedback, prioritize missing keywords
    ats_feedback = state.get("ats_feedback") or {}
    missing_skills = ats_feedback.get("missing_keywords", [])
    combined_search_skills = list(set(required_skills + missing_skills))

    matched_blocks = await search_cv_blocks(
        user_id=user_id,
        required_skills=combined_search_skills,
        limit=4,
    )

    current_revision = state.get("revision_count", 0) + 1

    # Format CV draft incorporating company context and matched blocks
    cv_draft = {
        "candidate_title": job.get("title", "Senior AI Engineer"),
        "target_company": job.get("company_name", "Target Company"),
        "professional_summary": (
            f"Results-oriented {job.get('title', 'Engineer')} with proven mastery "
            f"in {', '.join(combined_search_skills[:3])}. Specialized in stateful "
            f"systems, scalable backend APIs, and distributed architectures."
        ),
        "experience_blocks": matched_blocks,
        "skills_highlighted": combined_search_skills,
        "revision_version": current_revision,
    }

    return {
        "matched_cv_blocks": matched_blocks,
        "cv_draft": cv_draft,
        "revision_count": current_revision,
        "status": "cv_tailored",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Tailor node generated revision #{current_revision} "
                    f"with {len(matched_blocks)} matched achievement blocks."
                ),
            }
        ],
    }
