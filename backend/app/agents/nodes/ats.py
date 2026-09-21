"""ATS agent node simulating applicant tracking evaluation and cyclic scoring."""

from typing import Any

from app.agents.state import AgentState


async def ats_node(state: AgentState) -> dict[str, Any]:
    """Score the CV draft against job criteria and identify keyword gaps."""
    cv_draft = state.get("cv_draft") or {}
    job = state.get("job_details") or {}
    ats_reqs = job.get("ats_requirements") or {}
    required_skills = ats_reqs.get("required_skills", ["Python", "FastAPI"])

    highlighted = [s.lower() for s in cv_draft.get("skills_highlighted", [])]
    matched = [s for s in required_skills if s.lower() in highlighted]
    missing = [s for s in required_skills if s.lower() not in highlighted]

    revision = state.get("revision_count", 1)

    # Calculate weighted ATS score based on skill match and revisions
    base_match_ratio = len(matched) / max(len(required_skills), 1)

    if revision == 1 and missing:
        # First pass score under threshold if items are missing to trigger cyclic loop
        calculated_score = round(min(70.0, base_match_ratio * 75.0), 1)
    else:
        # Subsequent revisions or full match passes the >= 75.0% threshold
        calculated_score = round(
            min(95.0, 75.0 + (base_match_ratio * 20.0) + (revision * 5.0)), 1
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
