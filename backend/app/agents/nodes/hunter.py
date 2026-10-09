"""
Hunter agent node discovering, ranking, and selecting target job listings.

The hunter node acts as the candidate's proactive scout. It queries JobSourcePort
to search local PostgreSQL synced listings (and hermetic fallbacks) matching the
candidate's target role, location, and visa constraints.

Semantic pgvector Ranking:
  - When multiple listings match, Hunter retrieves the candidate's CV achievement
    blocks (from ``cv_block`` via pgvector or keyword search) and computes a
    composite semantic fit score combining 1536-dimensional cosine similarity,
    required skills overlap, and preferred skills overlap.
  - Hunter selects the listing with the highest composite fit score rather than
    arbitrarily selecting the first item in the result set.

Target Preservation:
  - If the execution state already specifies an explicit target job (via
    ``current_job_id`` or pre-populated ``job_details``), Hunter verifies or
    retrieves the authoritative listing via ``JobSourcePort.get_job`` while
    preserving caller-supplied criteria.
"""

from typing import Any

from app.agents.state import AgentState
from app.agents.tools.embeddings import embed_text
from app.agents.tools.vector_search import search_cv_blocks
from app.ingestion.api import JobListingDTO, get_default_job_source


async def hunter_node(state: AgentState) -> dict[str, Any]:
    """
    Execute job board search and semantic pgvector ranking against candidate profile.

    Reads:
      - ``job_details``: Target query parameters or pre-populated job criteria.
      - ``current_job_id``: Existing job ID if user manually specified a target.
      - ``user_id``: Candidate identifier used to retrieve career blocks.
      - ``visa_required``: Boolean work authorization constraint.

    Writes:
      - ``current_job_id``: Selected job identifier.
      - ``job_details``: Grounded listing attributes with semantic fit metrics.
      - ``status``: Set to ``"jobs_discovered"``.
      - ``messages``: System log documenting ranking evaluation and top selection.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update containing discovered job details and ranking logs.
    """
    job_details = state.get("job_details") or {}
    target_job_id = state.get("current_job_id") or job_details.get("id")
    user_id = state.get("user_id")
    job_source = get_default_job_source()

    # 1. If explicit target job ID is provided, look up authoritative record
    if target_job_id:
        found_job = await job_source.get_job(str(target_job_id))
        if found_job:
            selected_job = found_job.model_dump()
            for k, v in job_details.items():
                if v and k not in selected_job:
                    selected_job[k] = v
            resolved_job_id = str(selected_job.get("id") or target_job_id)
            selected_job["id"] = resolved_job_id
            return {
                "current_job_id": resolved_job_id,
                "job_details": selected_job,
                "status": "jobs_discovered",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Hunter retrieved and preserved target job: "
                            f"'{selected_job.get('title', 'Target Role')}' at "
                            f"'{selected_job.get('company_name')}' via JobSourcePort."
                        ),
                    }
                ],
            }

    # 2. Preserve caller-supplied target job details if complete
    has_company = bool(job_details.get("company_name"))
    has_requirements = bool(job_details.get("ats_requirements"))
    if has_company and (has_requirements or target_job_id):
        selected_job = dict(job_details)
        resolved_val = target_job_id or selected_job.get("id")
        resolved_target_id: str | None = (
            str(resolved_val) if resolved_val is not None else None
        )
        if resolved_target_id and not selected_job.get("id"):
            selected_job["id"] = resolved_target_id
        return {
            "current_job_id": resolved_target_id,
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

    # 3. Query local synced jobs or fixtures via JobSourcePort
    query = job_details.get("title", "Senior AI Engineer")
    location = job_details.get("location", "Remote")
    visa_req = state.get("visa_required", job_details.get("visa_required", False))

    matched_dtos: list[JobListingDTO] = await job_source.search_jobs(
        query=query,
        location=location,
        visa_required=visa_req,
    )

    if not matched_dtos:
        return {
            "current_job_id": None,
            "job_details": {},
            "status": "jobs_discovered",
            "messages": [
                {
                    "role": "system",
                    "content": f"Hunter found 0 matching jobs for query '{query}'.",
                }
            ],
        }

    # 4. Retrieve candidate CV blocks for semantic ranking
    candidate_blocks = await search_cv_blocks(user_id=user_id, limit=10)

    # 5. Perform semantic pgvector ranking against candidate CV blocks
    if candidate_blocks and len(matched_dtos) > 1:
        cand_skills = {s.lower() for b in candidate_blocks for s in b.get("skills", [])}
        cand_text = " ".join(
            f"{b.get('title', '')} {b.get('content', '')} "
            f"{' '.join(b.get('skills', []))}"
            for b in candidate_blocks
        )
        cand_embedding = await embed_text(cand_text)

        ranked_jobs: list[dict[str, Any]] = []
        for dto in matched_dtos:
            job_dict = dto.model_dump()
            req_skills = [
                s.lower()
                for s in job_dict.get("ats_requirements", {}).get("required_skills", [])
            ]
            pref_skills = [
                s.lower()
                for s in job_dict.get("ats_requirements", {}).get(
                    "preferred_skills", []
                )
            ]

            job_text = (
                f"{job_dict.get('title', '')} "
                f"{job_dict.get('raw_description', '')[:500]} "
                f"{' '.join(req_skills)}"
            )
            job_embedding = await embed_text(job_text)

            # Cosine similarity between unit-normalized vectors
            cos_sim = sum(
                a * b for a, b in zip(cand_embedding, job_embedding, strict=False)
            )
            norm_cos = max(
                0.0, min(1.0, (cos_sim + 1.0) / 2.0 if cos_sim < 0 else cos_sim)
            )

            # Skill overlap
            req_overlap = (
                len(cand_skills.intersection(req_skills)) / len(req_skills)
                if req_skills
                else 0.5
            )
            pref_overlap = (
                len(cand_skills.intersection(pref_skills)) / len(pref_skills)
                if pref_skills
                else 0.0
            )

            # Composite match: 50% vector similarity, 40% required skills, 10% preferred
            composite_score = round(
                ((0.5 * norm_cos) + (0.4 * req_overlap) + (0.1 * pref_overlap)) * 100,
                1,
            )
            job_dict["match_score"] = composite_score
            job_dict["semantic_fit"] = round(norm_cos * 100, 1)
            job_dict["skill_overlap"] = round(req_overlap * 100, 1)
            ranked_jobs.append(job_dict)

        ranked_jobs.sort(key=lambda j: j.get("match_score", 0.0), reverse=True)
        selected_job = ranked_jobs[0]
        score_val = selected_job.get("match_score", 0.0)
        system_log = (
            f"Hunter evaluated {len(matched_dtos)} matching job(s) and ranked them "
            f"against {len(candidate_blocks)} candidate CV blocks via pgvector "
            f"semantic scoring. Selected top fit: '{selected_job.get('title')}' at "
            f"'{selected_job.get('company_name')}' (match score: {score_val}%)."
        )
    else:
        selected_job = matched_dtos[0].model_dump()
        system_log = (
            f"Hunter discovered {len(matched_dtos)} matching job(s). "
            f"Selected target: '{selected_job.get('title')}' at "
            f"'{selected_job.get('company_name')}'."
        )

    current_job_id = selected_job.get("id")

    return {
        "current_job_id": current_job_id,
        "job_details": selected_job,
        "status": "jobs_discovered",
        "messages": [
            {
                "role": "system",
                "content": system_log,
            }
        ],
    }
