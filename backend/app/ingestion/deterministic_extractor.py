"""
Deterministic requirements extraction and visa status classification.

Pass 1 of the extraction pipeline:
- High-precision matching against curated skills taxonomy.
- Years of experience extraction via robust regex patterns.
- Tri-state visa sponsorship policy classification (yes / no / unknown).
"""

import re

from app.ingestion.models import ParsedRequirementsDTO, VisaSponsorshipStatus
from app.ingestion.taxonomy import SKILL_TAXONOMY

# Regex for years of experience
# (e.g., "5+ years", "3-5 years of experience", "at least 4 years")
YOE_PATTERNS = [
    re.compile(
        r"(\d+)\s*\+?\s*years?(?:\s+(?:of|in))?(?:\s+[\w\-]+)*\s+experience", re.I
    ),
    re.compile(r"(\d+)\s*\+?\s*years?", re.I),
    re.compile(r"at\s+least\s+(\d+)\s*years?", re.I),
    re.compile(r"minimum\s+(?:of\s+)?(\d+)\s*years?", re.I),
    re.compile(r"(\d+)\s*-\s*\d+\s*years?", re.I),
]

# Patterns for negative visa sponsorship ("no")
VISA_NEGATIVE_PATTERNS = [
    re.compile(r"(?:will\s+not|cannot|unable\s+to|not\s+able\s+to)\s+sponsor", re.I),
    re.compile(r"no\s+(?:visa\s+)?sponsorship\s+(?:is\s+)?available", re.I),
    re.compile(r"without\s+(?:the\s+need\s+for\s+)?sponsorship", re.I),
    re.compile(
        r"must\s+be\s+authorized\s+to\s+work\s+without\s+(?:company\s+)?sponsorship",
        re.I,
    ),
    re.compile(r"not\s+offering\s+sponsorship", re.I),
]

# Patterns for positive visa sponsorship ("yes")
VISA_POSITIVE_PATTERNS = [
    re.compile(r"visa\s+sponsorship\s+(?:is\s+)?available", re.I),
    re.compile(r"(?:can|will|able\s+to)\s+sponsor(?:\s+(?:work\s+)?visas?)?", re.I),
    re.compile(r"sponsorship\s+is\s+provided", re.I),
    re.compile(r"willing\s+to\s+sponsor", re.I),
    re.compile(r"relocation\s+and\s+visa\s+sponsorship", re.I),
]


def classify_visa_sponsorship(text: str) -> VisaSponsorshipStatus:
    """
    Classify visa sponsorship as YES, NO, or UNKNOWN based on text evidence.
    Negative patterns take priority to protect candidate from ineligible roles.
    """
    if not text:
        return VisaSponsorshipStatus.UNKNOWN

    for pat in VISA_NEGATIVE_PATTERNS:
        if pat.search(text):
            return VisaSponsorshipStatus.NO

    for pat in VISA_POSITIVE_PATTERNS:
        if pat.search(text):
            return VisaSponsorshipStatus.YES

    return VisaSponsorshipStatus.UNKNOWN


def extract_years_of_experience(text: str) -> int | None:
    """
    Extract minimum required years of experience from description text.
    """
    if not text:
        return None

    yoe_found: list[int] = []
    for pat in YOE_PATTERNS:
        matches = pat.findall(text)
        for m in matches:
            try:
                yoe_found.append(int(m))
            except ValueError:
                pass

    if yoe_found:
        # Return reasonable minimum (between 1 and 20)
        valid = [y for y in yoe_found if 1 <= y <= 20]
        if valid:
            return min(valid)
    return None


def extract_deterministic_requirements(
    title: str,
    raw_description: str,
) -> ParsedRequirementsDTO:
    """
    Deterministic Pass 1:
    Extracts skills, minimum experience, and visa status without any LLM cost.
    """
    combined_text = f"{title}\n{raw_description}"
    words_boundary_text = f" {combined_text.lower()} "

    detected_skills: list[str] = []
    evidence: dict[str, list[str]] = {}

    for canonical_name, aliases in SKILL_TAXONOMY.items():
        matched_aliases: list[str] = []
        for alias in aliases:
            # Word boundary check to prevent substring false-positives
            pattern = rf"(?:\b|_){re.escape(alias.lower())}(?:\b|_)"
            if re.search(pattern, words_boundary_text):
                matched_aliases.append(alias)

        if matched_aliases:
            detected_skills.append(canonical_name)
            evidence[canonical_name] = matched_aliases

    # Sort alphabetically for consistency
    detected_skills.sort()

    yoe = extract_years_of_experience(combined_text)
    visa_status = classify_visa_sponsorship(combined_text)

    return ParsedRequirementsDTO(
        required_skills=detected_skills,
        preferred_skills=[],
        min_experience_years=yoe,
        visa_sponsorship=visa_status,
        extraction_version="v1-deterministic",
        confidence_score=0.95 if detected_skills else 0.5,
        needs_review=False,
        evidence=evidence,
    )
