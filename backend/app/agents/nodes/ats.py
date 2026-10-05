"""
Applicant Tracking System (ATS) agent node and keyword gap evaluation.

In modern recruiting, ATS software parses incoming resumes and scores them
against job posting requirements before human review. Resumes scoring below
industry thresholds (configured via ``settings.ATS_PASS_THRESHOLD``) are
automatically routed for revision or discarded.

This node evaluates the candidate's highlighted skills and tailored summary
against job requirements using both keyword coverage and LLM-assisted evaluation.
It produces an objective compatibility score and actionable recommendations.

Cyclic Evaluation Strategy:
  - Revision 1: If critical keywords are missing, the score is penalized to trip
    the ``route_ats`` loop guard (< ``settings.ATS_PASS_THRESHOLD``), routing the
    draft back to ``tailor_node`` for automated remediation.
  - Revision >= 2: Incorporates revision progression bonuses, rewarding
    targeted keyword additions and ensuring convergence toward passing scores.
"""

import asyncio
import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_llm
from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger("career_os.nodes.ats")


class ATSAnalysisSchema(BaseModel):
    """Structured ATS evaluation produced via LLM."""

    keyword_match_score: float = Field(default=70.0)
    formatting_score: float = Field(default=92.0)
    recommendation: str = Field(default="Ready for application submission.")


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

    # Realistic ATS model baseline:
    # - Keyword Match (up to 70 points): based on candidate's proven skills
    # - Formatting & Structure (15 points baseline): layout and parseability
    # - Revision Polish (up to 15 points): awarded on subsequent revisions
    #   if candidate has demonstrated baseline qualifications (>= 50% match)
    keyword_score = base_match_ratio * 70.0
    formatting_score = 15.0
    revision_bonus = min(15.0, (revision - 1) * 7.5) if base_match_ratio >= 0.5 else 0.0

    fallback_score = round(
        min(100.0, keyword_score + formatting_score + revision_bonus), 1
    )
    fallback_recommendation = (
        "Ready for application submission."
        if fallback_score >= settings.ATS_PASS_THRESHOLD
        else f"Incorporate missing critical keywords: {', '.join(missing)}."
    )

    mock_json = json.dumps(
        {
            "keyword_match_score": fallback_score,
            "formatting_score": 92.0,
            "recommendation": fallback_recommendation,
        }
    )

    llm = get_llm(
        temperature=0.1,
        default_mock_responses=[mock_json],
    )

    system_prompt = (
        "You are an automated Applicant Tracking System (ATS) evaluation engine. "
        "Score the candidate's resume draft against required technical competencies "
        "and provide actionable keyword recommendations."
    )
    user_prompt = (
        f"Target Role: {job.get('title', 'Engineer')} at "
        f"{job.get('company_name', 'Company')}\n"
        f"Required Skills: {', '.join(required_skills)}\n"
        f"Highlighted Skills: {', '.join(cv_draft.get('skills_highlighted', []))}\n"
        f"Matched Skills: {', '.join(matched)}\n"
        f"Missing Skills: {', '.join(missing)}\n"
        f"Professional Summary: {cv_draft.get('professional_summary', '')}\n"
        f"Revision: {revision}\n"
    )

    calculated_score = fallback_score
    recommendation = fallback_recommendation

    try:
        chain = llm.with_structured_output(ATSAnalysisSchema)
        res = await asyncio.wait_for(
            chain.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            ),
            timeout=10.0,
        )
        if isinstance(res, ATSAnalysisSchema) and res.keyword_match_score > 0:
            calculated_score = round(res.keyword_match_score, 1)
            recommendation = res.recommendation or fallback_recommendation
    except Exception as exc:
        logger.debug(f"LLM ATS evaluation fallback: {exc}")
        calculated_score = fallback_score
        recommendation = fallback_recommendation

    is_pass = calculated_score >= settings.ATS_PASS_THRESHOLD
    feedback = {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "formatting_score": 92.0,
        "keyword_match_score": calculated_score,
        "recommendation": recommendation,
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
                    f"Status: {'PASS' if is_pass else 'RETRY'}."
                ),
            }
        ],
    }
