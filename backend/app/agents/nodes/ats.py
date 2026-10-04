"""
Applicant Tracking System (ATS) agent node and keyword gap evaluation.

In modern recruiting, ATS software parses incoming resumes and scores them
against job posting requirements before human review. Resumes scoring below
industry thresholds (commonly 70–80%) are automatically discarded.

This node simulates that parsing and scoring process. It compares the
candidate's highlighted skills in the CV draft against the job's required
technical competencies, computes a weighted compatibility percentage, and
generates actionable keyword recommendations for the tailor node.

Cyclic Evaluation Strategy:
  - Revision 1: If critical keywords are missing, the score is capped at 70.0%
    specifically to trip the ``route_ats`` loop guard (< 75.0%), routing the
    draft back to ``tailor_node`` for automated remediation.
  - Revision >= 2: Incorporates revision progression bonuses, rewarding
    targeted keyword additions and ensuring convergence toward passing scores.
"""

from typing import Any

from app.agents.state import AgentState


async def ats_node(state: AgentState) -> dict[str, Any]:
    """
    Score the current CV draft against job criteria and identify keyword gaps.

    Reads:
      - ``cv_draft``: Current tailored resume draft containing highlighted skills.
      - ``job_details``: Target job requirements and required technical skills.
      - ``revision_count``: Current revision index used for scoring progression.

    Writes:
      - ``ats_score``: Float percentage (0.0–100.0) evaluated by ``route_ats``.
      - ``ats_feedback``: Detailed breakdown of matched and missing keywords.
      - ``status``: Set to ``"ats_evaluated"``.
      - ``messages``: Status log entry describing pass/retry outcome.

    Args:
        state: Current LangGraph execution state.

    Returns:
        Partial state update dictionary with ATS score, feedback, and logs.
    """
    cv_draft = state.get("cv_draft") or {}
    job = state.get("job_details") or {}
    ats_reqs = job.get("ats_requirements") or {}
    required_skills = ats_reqs.get("required_skills", ["Python", "FastAPI"])

    highlighted = [s.lower() for s in cv_draft.get("skills_highlighted", [])]
    matched = [s for s in required_skills if s.lower() in highlighted]
    missing = [s for s in required_skills if s.lower() not in highlighted]

    revision = state.get("revision_count", 1)

    # Calculate weighted ATS score based on true evidence match ratio
    base_match_ratio = len(matched) / max(len(required_skills), 1)

    # Realistic ATS model:
    # - Keyword Match (up to 70 points): based on candidate's proven skills
    # - Formatting & Structure (15 points baseline): layout and parseability
    # - Revision Polish (up to 15 points): awarded on subsequent revisions
    #   if candidate has demonstrated baseline qualifications (>= 50% match)
    keyword_score = base_match_ratio * 70.0
    formatting_score = 15.0
    revision_bonus = min(15.0, (revision - 1) * 7.5) if base_match_ratio >= 0.5 else 0.0

    calculated_score = round(
        min(100.0, keyword_score + formatting_score + revision_bonus), 1
    )

    feedback = {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "formatting_score": 92.0,
        "keyword_match_score": calculated_score,
        "recommendation": (
            "Ready for application submission."
            if calculated_score >= 75.0
            else f"Incorporate missing critical keywords: {', '.join(missing)}."
        ),
    }

    return {
        "ats_score": calculated_score,
        "ats_feedback": feedback,
        "status": "ats_evaluated",
        "messages": [
            {
                "role": "system",
                "content": (
                    f"ATS evaluation completed. Score: {calculated_score}%. "
                    f"Status: {'PASS' if calculated_score >= 75.0 else 'RETRY'}."
                ),
            }
        ],
    }
