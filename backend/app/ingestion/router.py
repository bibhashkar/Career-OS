"""
Jev-style decision-native document triage and ingestion strategy router.
Evaluates layout complexity, format indicators, and text density to dispatch
the resume to the optimal extraction pipeline with minimal latency.
"""

import logging
import re
from typing import Any

from app.schemas.candidate_dossier import (
    ExperienceDensity,
    LayoutType,
    ResumeTriageDecision,
)

logger = logging.getLogger("career_os.ingestion.router")

LINKEDIN_INDICATORS = [
    "www.linkedin.com/in/",
    "linkedin.com/in/",
    "Top Skills",
    "Languages",
    "Certifications",
    "Contact",
]

ACADEMIC_INDICATORS = [
    "publications",
    "peer-reviewed",
    "curriculum vitae",
    "dissertation",
    "thesis",
    "proceedings",
    "journal articles",
    "conference proceedings",
    "fellowship",
]


def detect_is_linkedin_pdf(text: str) -> bool:
    """
    Detect whether text conforms to LinkedIn's 'Save to PDF' export format.
    """
    matches = sum(1 for ind in LINKEDIN_INDICATORS if ind in text)
    return matches >= 2


def triage_resume_layout(
    raw_text: str,
    filename: str = "",
    llm: Any | None = None,
) -> ResumeTriageDecision:
    """
    Fast, deterministic triage router evaluating document structure and
    recommending the optimal extraction strategy.
    """
    clean_text = raw_text.strip()
    char_len = len(clean_text)
    lower = clean_text.lower()

    # 1. Scanned / Empty Text layer detection
    if char_len < 60:
        return ResumeTriageDecision(
            layout_type="scanned_image_pdf",
            recommended_pipeline="vision_ocr_pipeline",
            has_text_layer=False,
            is_multi_column=False,
            estimated_experience_density="entry",
            confidence_score=0.95,
            reasoning="Extracted text layer is nearly empty; document requires OCR / Vision pipeline.",
        )

    # 2. LinkedIn PDF Export Detection
    if detect_is_linkedin_pdf(clean_text):
        return ResumeTriageDecision(
            layout_type="linkedin_pdf_export",
            recommended_pipeline="linkedin_specialized",
            has_text_layer=True,
            is_multi_column=False,
            estimated_experience_density="mid",
            confidence_score=0.98,
            reasoning="Matched distinctive LinkedIn PDF export headings and structure.",
        )

    # 3. Academic Curriculum Vitae Detection
    academic_matches = sum(1 for ind in ACADEMIC_INDICATORS if ind in lower)
    if academic_matches >= 2 and char_len > 3500:
        return ResumeTriageDecision(
            layout_type="academic_curriculum_vitae",
            recommended_pipeline="deep_llm_structured",
            has_text_layer=True,
            is_multi_column=False,
            estimated_experience_density="senior_staff",
            confidence_score=0.90,
            reasoning="Detected academic curriculum vitae indicators (publications, dissertation, research).",
        )

    # 4. Multi-column / Tabular / Complex formatting detection
    lines = clean_text.split("\n")
    pipe_count = sum(line.count("|") for line in lines[:25])
    short_line_density = sum(1 for line in lines if 0 < len(line.strip()) < 30) / max(
        1, len(lines)
    )
    is_multi_column = pipe_count >= 5 or short_line_density > 0.45

    # 5. Experience Density Estimation
    yoe_match = re.search(
        r"\b(\d{1,2})\+?\s*(?:years|yrs)\b", clean_text, re.IGNORECASE
    )
    estimated_density: ExperienceDensity = "mid"
    if yoe_match:
        yoe_num = int(yoe_match.group(1))
        if yoe_num >= 10:
            estimated_density = "senior_staff"
        elif yoe_num >= 4:
            estimated_density = "mid"
        else:
            estimated_density = "entry"
    elif any(
        k in lower
        for k in (
            "principal",
            "staff engineer",
            "director",
            "head of",
            "architect",
            "lead engineer",
        )
    ):
        estimated_density = "senior_staff"
    elif any(
        k in lower
        for k in (
            "student",
            "intern",
            "junior",
            "new grad",
            "bachelor of",
            "expected 202",
        )
    ):
        estimated_density = "entry"

    layout_type: LayoutType = (
        "multi_column_creative" if is_multi_column else "standard_single_column"
    )

    return ResumeTriageDecision(
        layout_type=layout_type,
        recommended_pipeline="deep_llm_structured",
        has_text_layer=True,
        is_multi_column=is_multi_column,
        estimated_experience_density=estimated_density,
        confidence_score=0.92,
        reasoning=f"Analyzed {len(lines)} lines with {char_len} chars. Experience density: {estimated_density}.",
    )
