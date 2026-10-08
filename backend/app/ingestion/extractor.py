"""
Hybrid requirements extractor with LLM pass and grounding validation.

Architecture:
1. Pass 1 (Deterministic): Extract initial candidate skills from taxonomy,
   years of experience, and visa status.
2. Pass 2 (LLM - Gemini Flash): Structured extraction distinguishing
   required vs. preferred skills and nuanced requirements.
3. Grounding Validation: Verifies that every skill output by the LLM is
   grounded in the source text (via exact, lowercase, or alias matching).
   Hallucinated skills are discarded.
4. Starvation prevention: If LLM fails or is unconfigured, falls back
   cleanly to Pass 1 results rather than returning empty lists or hardcoded values.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.ingestion.deterministic_extractor import (
    extract_deterministic_requirements,
)
from app.ingestion.models import ParsedRequirementsDTO, VisaSponsorshipStatus
from app.ingestion.ports.provider import RequirementsExtractorPort
from app.ingestion.taxonomy import SKILL_TAXONOMY

logger = logging.getLogger("career_os.ingestion.extractor")

SYSTEM_EXTRACTION_PROMPT = """
You are an expert technical ATS requirements extraction engine.
Analyze the provided Job Description and output ONLY a valid JSON object:
{
  "required_skills": ["List", "of", "strictly", "required", "technical", "skills"],
  "preferred_skills": ["List", "of", "nice-to-have", "skills"],
  "min_experience_years": 4, // integer or null
  "visa_sponsorship": "yes" | "no" | "unknown"
}
Rules:
1. Do NOT hallucinate skills that do not appear in the text.
2. Maintain standard technical capitalization (e.g. Python, PostgreSQL, Docker).
3. If no skills are mentioned, output empty arrays.
4. Output valid JSON with no markdown formatting or extra commentary.
"""


class HybridRequirementsExtractor(RequirementsExtractorPort):
    """
    Two-pass requirements extraction with grounding validation.
    """

    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def _is_grounded_in_text(self, skill: str, text: str) -> bool:
        """
        Check if a candidate skill from the LLM is grounded in the source text.
        """
        s_lower = skill.lower()
        t_lower = text.lower()

        # Direct occurrence check
        if s_lower in t_lower:
            return True

        # Check aliases in taxonomy
        for canonical, aliases in SKILL_TAXONOMY.items():
            if s_lower == canonical.lower() or s_lower in [a.lower() for a in aliases]:
                for alias in aliases:
                    if alias.lower() in t_lower:
                        return True

        return False

    async def extract_requirements(
        self,
        title: str,
        raw_description: str,
        company_name: str,
    ) -> ParsedRequirementsDTO:
        # Pass 1: Deterministic extraction (always runs)
        deterministic_res = extract_deterministic_requirements(title, raw_description)
        combined_text = f"{title}\n{raw_description}"

        # If LLM is not provided, initialize standard Gemini LLM
        llm = self.llm or get_llm(temperature=0.0)

        try:
            prompt = (
                f"Job Title: {title}\nCompany: {company_name}\n\n"
                f"Job Description:\n{raw_description[:4000]}"
            )
            response = await llm.ainvoke(
                [
                    SystemMessage(content=SYSTEM_EXTRACTION_PROMPT),
                    HumanMessage(content=prompt),
                ]
            )
            raw_content = getattr(response, "content", response)
            raw_text = str(raw_content)
            clean_json = (
                raw_text.strip().replace("```json", "").replace("```", "").strip()
            )
            data = json.loads(clean_json)

            # Grounding Validation: discard any skills not present in text
            llm_required = [
                s
                for s in data.get("required_skills", [])
                if self._is_grounded_in_text(s, combined_text)
            ]
            llm_preferred = [
                s
                for s in data.get("preferred_skills", [])
                if self._is_grounded_in_text(s, combined_text)
            ]

            # Merge with deterministic skills to ensure zero starvation
            all_detected = set(deterministic_res.required_skills)
            merged_required = list(set(llm_required).union(all_detected))
            merged_required.sort()

            # Visa classification: combine deterministic with LLM recommendation
            llm_visa_str = data.get("visa_sponsorship", "unknown").lower()
            final_visa: VisaSponsorshipStatus
            if deterministic_res.visa_sponsorship != VisaSponsorshipStatus.UNKNOWN:
                final_visa = deterministic_res.visa_sponsorship
            elif llm_visa_str in ("yes", "no"):
                final_visa = VisaSponsorshipStatus(llm_visa_str)
            else:
                final_visa = VisaSponsorshipStatus.UNKNOWN

            yoe = (
                data.get("min_experience_years")
                or deterministic_res.min_experience_years
            )

            return ParsedRequirementsDTO(
                required_skills=merged_required,
                preferred_skills=llm_preferred,
                min_experience_years=yoe,
                visa_sponsorship=final_visa,
                extraction_version="v1-hybrid",
                confidence_score=0.98 if merged_required else 0.6,
                needs_review=False,
                evidence=deterministic_res.evidence,
            )

        except Exception as e:
            logger.warning(
                "LLM extraction pass failed; falling back to deterministic: %s",
                e,
            )
            return deterministic_res
