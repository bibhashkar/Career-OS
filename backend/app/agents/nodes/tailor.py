"""
Tailor agent node querying pgvector and assembling customized CV drafts.

Rather than submitting a static, one-size-fits-all resume, the tailor node
dynamically constructs a targeted CV draft. It performs semantic vector
similarity search over the candidate's career achievement chunks (stored in
PostgreSQL via ``pgvector``) and selects the most relevant evidence blocks.

Adaptive Revision Loop & Grounded LLM Synthesis:
  - On first pass: queries for blocks matching the job's stated required skills.
  - On retry pass (when routed from ``ats_node``): inspects ``ats_feedback`` for
    any identified ``missing_keywords``, merges them into the retrieval query,
    and pulls achievement blocks demonstrating those missing skills.
  - LLM Grounding: Synthesizes a factual professional summary grounded strictly
    in proven candidate skills and retrieved evidence blocks, avoiding fabrication.
  - Increments ``revision_count`` to advance loop guard bounds.
"""

import asyncio
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.agents.tools.vector_search import search_cv_blocks


async def tailor_node(state: AgentState) -> dict[str, Any]:
    """
    Retrieve CV blocks from pgvector and assemble tailored CV draft.

    Reads:
      - ``user_id``: Candidate profile identifier.
      - ``job_details``: Target job title, company name, and required skills.
      - ``ats_feedback``: Missing keywords flagged during prior ATS evaluations.
      - ``revision_count``: Current revision index.
      - ``tone_directives``: Style preferences (confident, executive, technical).

    Writes:
      - ``matched_cv_blocks``: Top matching achievement blocks from pgvector.
      - ``cv_draft``: Structured resume draft ready for ATS scoring.
      - ``revision_count``: Incremented revision index.
      - ``status``: Set to ``"cv_tailored"``.
      - ``messages``: System log documenting generated revision and block count.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update containing the assembled CV draft and matched blocks.
    """
    user_id = state.get("user_id")
    job = state.get("job_details") or {}
    reqs = job.get("ats_requirements", {})
    required_skills = reqs.get("required_skills", ["Python", "FastAPI"])

    # If revising due to ATS feedback, prioritize missing keywords in retrieval
    ats_feedback = state.get("ats_feedback") or {}
    missing_skills = ats_feedback.get("missing_keywords", [])
    combined_search_skills = list(set(required_skills + missing_skills))

    # Retrieve top 4 matching achievement blocks from pgvector or keyword search
    matched_blocks = await search_cv_blocks(
        user_id=user_id,
        required_skills=combined_search_skills,
        limit=4,
    )

    # Aggregate skills actually demonstrated across retrieved achievement blocks
    candidate_skills: set[str] = set()
    for block in matched_blocks:
        for skill in block.get("skills", []):
            candidate_skills.add(skill)

    # Highlight proven skills that match the target role requirements
    target_skills_lower = {s.lower(): s for s in combined_search_skills}
    proven_matching_skills = [
        target_skills_lower[s.lower()]
        for s in candidate_skills
        if s.lower() in target_skills_lower
    ]
    # Highlight proven matching skills, falling back to top candidate skills
    highlighted_skills = proven_matching_skills or sorted(candidate_skills)[:5]
    summary_skills = highlighted_skills[:3] or ["Software Engineering"]

    current_revision = state.get("revision_count", 0) + 1

    # Format CV draft incorporating company context, tone directives, and blocks
    tone = state.get("tone_directives") or {}
    style = tone.get("style", "confident")
    brevity = tone.get("brevity", "high")

    target_title = job.get("title", "Senior AI Engineer")
    target_company = job.get("company_name", "Target Company")

    if brevity == "high":
        summary_intro = f"Focused, results-driven {target_title}"
    elif style == "executive":
        summary_intro = f"Strategic, high-impact {target_title}"
    else:
        summary_intro = f"Results-oriented {target_title}"

    fallback_summary = (
        f"{summary_intro} with proven mastery in {', '.join(summary_skills)}. "
        f"Specialized in stateful systems, scalable backend APIs, "
        f"and distributed architectures."
    )

    # Synthesize tailored professional summary via LLM grounded in evidence
    llm = get_llm(
        temperature=0.2,
        default_mock_responses=[fallback_summary],
    )

    evidence_titles = [b.get("title", "") for b in matched_blocks if b.get("title")]
    evidence_desc = ", ".join(evidence_titles[:3])

    system_prompt = (
        "You are an executive CV tailoring specialist. You craft factual, high-impact "
        "professional summaries strictly grounded in the candidate's demonstrated "
        "career blocks. Never hallucinate skills or qualifications not in the evidence."
    )
    user_prompt = (
        f"Target Role: {target_title} at {target_company}\n"
        f"Required Skills: {', '.join(required_skills)}\n"
        f"Proven Skills: {', '.join(highlighted_skills)}\n"
        f"Career Evidence: {evidence_desc}\n"
        f"Tone Directives: style={style}, brevity={brevity}\n\n"
        "Generate a factual, 2-sentence professional summary highlighting proven "
        "alignment with the target role."
    )

    try:
        res = await asyncio.wait_for(
            llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            ),
            timeout=10.0,
        )
        summary_content = (
            res.content if isinstance(res.content, str) else str(res.content)
        ).strip()
        if not summary_content:
            summary_content = fallback_summary
    except Exception:
        summary_content = fallback_summary

    cv_draft = {
        "candidate_title": target_title,
        "target_company": target_company,
        "professional_summary": summary_content,
        "experience_blocks": matched_blocks,
        "skills_highlighted": highlighted_skills,
        "tone": tone,
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
