"""
Resume and document parsing engine for multi-modal candidate onboarding.

This module implements candidate document ingestion documented in ADR-007:
  - Positional text extraction from PDF via ``pdfplumber`` (prevents column scrambling).
  - Structured text extraction from DOCX via ``python-docx``.
  - Specialized heuristic detector and parser for LinkedIn "Save to PDF" exports.
  - Atomic CV block decomposition: category tagging, STAR breakdown, metrics.
  - Skill taxonomy normalization using ``app.ingestion.taxonomy.SKILL_TAXONOMY``.
"""

import io
import re
from typing import Any

import docx
import pdfplumber
from pydantic import BaseModel, Field

from app.ingestion.taxonomy import SKILL_TAXONOMY

# Common metric detection regular expressions
RE_PERCENTAGE = re.compile(
    r"\b(\d+(?:\.\d+)?%\s*(?:reduction|increase|improvement|growth|boost|drop)?)\b",
    re.IGNORECASE,
)
RE_CURRENCY = re.compile(r"(\$[\d,]+(?:\.\d+)?[KkMmBb]?)")
RE_MULTIPLIER = re.compile(r"\b(\d+(?:\.\d+)?x)\b", re.IGNORECASE)
RE_LATENCY_THROUGHPUT = re.compile(
    r"\b(\d+[\d,]*(?:[KkMmBb])?\s*"
    r"(?:ms|milliseconds|seconds|req\/s|rps|qps|queries\/sec|events\/sec))\b",
    re.IGNORECASE,
)
RE_SCALE_USERS = re.compile(
    r"\b(\d+[\d,]*\+?\s*"
    r"(?:users|active users|dau|mau|records|stars|downloads|clients))\b",
    re.IGNORECASE,
)
RE_HACKATHON_HONORS = re.compile(
    r"\b(1st\s*place|2nd\s*place|3rd\s*place|first\s*place|second\s*place|third\s*place|"
    r"top\s*\d+|winner|finalist|champion|best\s*hack|grand\s*prize)\b",
    re.IGNORECASE,
)

# Email and Contact regexes
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_PHONE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
RE_LINKEDIN = re.compile(r"linkedin\.com/in/([A-Za-z0-9_-]+)", re.IGNORECASE)
RE_GITHUB = re.compile(r"github\.com/([A-Za-z0-9_-]+)", re.IGNORECASE)

# Category classification triggers
HACKATHON_TRIGGERS = {
    "hackathon",
    "hackmit",
    "ethglobal",
    "calhacks",
    "treehacks",
    "pennapps",
    "devpost",
    "mlh",
    "kaggle",
    "competitive programming",
    "datathon",
    "icpc",
}
OPEN_SOURCE_TRIGGERS = {
    "open source",
    "open-source",
    "github stars",
    "maintainer",
    "contributor",
    "pull request",
    "oss",
}
EDUCATION_TRIGGERS = {
    "education",
    "university",
    "college",
    "bachelor",
    "master",
    "ph.d",
    "phd",
    "b.s.",
    "m.s.",
    "gpa",
}


class ParsedCVBlock(BaseModel):
    """
    Decomposed atomic career achievement block.
    """

    category: str = Field(
        ...,
        description=(
            "experience, project, education, hackathon_achievement, open_source"
        ),
    )
    title: str
    organization: str | None = None
    timeframe: str | None = None
    content: str
    star_breakdown: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    is_quantified: bool = False


class ParsedCandidateData(BaseModel):
    """
    Extracted candidate profile data synthesized from uploaded document.
    """

    full_name: str
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    detected_format: str = "generic_resume"
    skills: list[str] = Field(default_factory=list)
    blocks: list[ParsedCVBlock] = Field(default_factory=list)
    raw_text: str = ""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract positional text from PDF bytes using pdfplumber.
    """
    page_texts: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if text:
                page_texts.append(text)
            else:
                raw = page.extract_text()
                if raw:
                    page_texts.append(raw)
    return "\n\n".join(page_texts)


def extract_text_from_docx(docx_bytes: bytes) -> str:
    """
    Extract structured text from Word DOCX bytes using python-docx.
    """
    doc = docx.Document(io.BytesIO(docx_bytes))
    full_text: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                full_text.append(" | ".join(row_text))
    return "\n".join(full_text)


def detect_is_linkedin_pdf(text: str) -> bool:
    """
    Detect whether extracted text conforms to LinkedIn's 'Save to PDF' export layout.
    """
    indicators = [
        "www.linkedin.com/in/",
        "linkedin.com/in/",
        "Top Skills",
        "Languages",
        "Certifications",
        "Contact",
    ]
    matches = sum(1 for indicator in indicators if indicator in text)
    return matches >= 2


def extract_skills_from_text(text: str) -> list[str]:
    """
    Match and normalize canonical technical skills using SKILL_TAXONOMY.
    """
    found_skills: set[str] = set()
    lowered = text.lower()
    for canonical, aliases in SKILL_TAXONOMY.items():
        for alias in aliases:
            pattern = r"\b" + re.escape(alias.lower()) + r"\b"
            if re.search(pattern, lowered):
                found_skills.add(canonical)
                break
    return sorted(found_skills)


def extract_metrics(content: str) -> dict[str, Any]:
    """
    Detect concrete quantified achievements and business outcomes from text.
    """
    metrics: dict[str, Any] = {}

    pct_matches = RE_PERCENTAGE.findall(content)
    if pct_matches:
        metrics["percentage_impact"] = pct_matches[0]

    cur_matches = RE_CURRENCY.findall(content)
    if cur_matches:
        metrics["financial_impact"] = cur_matches[0]

    mul_matches = RE_MULTIPLIER.findall(content)
    if mul_matches:
        metrics["scale_multiplier"] = mul_matches[0]

    lat_matches = RE_LATENCY_THROUGHPUT.findall(content)
    if lat_matches:
        metrics["throughput_or_latency"] = lat_matches[0]

    scale_matches = RE_SCALE_USERS.findall(content)
    if scale_matches:
        metrics["user_or_data_scale"] = scale_matches[0]

    hack_matches = RE_HACKATHON_HONORS.findall(content)
    if hack_matches:
        metrics["honor_placement"] = hack_matches[0]

    return metrics


def synthesize_star_breakdown(
    bullet: str,
    detected_skills: list[str],
    metrics: dict[str, Any],
) -> dict[str, str]:
    """
    Decompose a bullet or achievement narrative into Situation, Task, Action, Result.
    """
    star: dict[str, str] = {
        "situation": "Target project initiative and architectural objectives.",
        "task": bullet.strip(),
        "action": f"Implemented solution utilizing {', '.join(detected_skills[:4])}."
        if detected_skills
        else "Executed key implementation deliverables.",
        "result": "Delivered production enhancements.",
    }

    if metrics:
        metric_values = list(metrics.values())
        star["result"] = f"Achieved measurable business impact: {metric_values[0]}."

    return star


def parse_linkedin_text(text: str) -> ParsedCandidateData:
    """
    Parse a standardized LinkedIn 'Save to PDF' document export.
    """
    full_name = "Candidate"
    email = None
    phone = None
    linkedin_url = None
    headline = None
    skills_list: list[str] = []
    blocks: list[ParsedCVBlock] = []

    # 1. Contact information extraction
    emails = RE_EMAIL.findall(text)
    if emails:
        email = emails[0]
    phones = RE_PHONE.findall(text)
    if phones:
        phone = phones[0]
    li_matches = RE_LINKEDIN.findall(text)
    if li_matches:
        linkedin_url = f"https://www.linkedin.com/in/{li_matches[0]}"

    # Look for candidate name
    # In LinkedIn exports, the name appears between Languages and Summary
    name_search_chunk = text
    if "Languages" in text:
        name_search_chunk = text.split("Languages", 1)[1]
    elif "Top Skills" in text:
        name_search_chunk = text.split("Top Skills", 1)[1]

    if "Summary" in name_search_chunk:
        name_search_chunk = name_search_chunk.split("Summary", 1)[0]
    elif "Experience" in name_search_chunk:
        name_search_chunk = name_search_chunk.split("Experience", 1)[0]

    known_lang_tokens = {
        "languages",
        "english",
        "spanish",
        "french",
        "german",
        "chinese",
        "hindi",
        "contact",
        "top skills",
        "summary",
        "experience",
    }
    candidate_lines = [
        cand_line.strip()
        for cand_line in name_search_chunk.split("\n")
        if cand_line.strip()
        and cand_line.lower() not in known_lang_tokens
        and "@" not in cand_line
        and "linkedin.com" not in cand_line
    ]

    for i, cand_line in enumerate(candidate_lines):
        if len(cand_line.split()) in [2, 3, 4] and not any(
            char.isdigit() for char in cand_line
        ):
            full_name = cand_line
            if i + 1 < len(candidate_lines):
                headline = candidate_lines[i + 1]
            break

    # Extract Top Skills section
    if "Top Skills" in text:
        after_top = text.split("Top Skills", 1)[1]
        skills_chunk = (
            after_top.split("Languages")[0]
            if "Languages" in after_top
            else after_top[:300]
        )
        for sline in skills_chunk.split("\n"):
            cand = sline.strip()
            if cand and len(cand) < 40 and not cand.startswith("http"):
                skills_list.append(cand)

    # 2. Section chunks
    exp_text = ""
    if "Experience" in text:
        after_exp = text.split("Experience", 1)[1]
        exp_text = (
            after_exp.split("Education")[0] if "Education" in after_exp else after_exp
        )

    # Parse experience blocks
    if exp_text:
        raw_items = [
            chunk.strip() for chunk in re.split(r"\n\s*\n", exp_text) if chunk.strip()
        ]
        for item_clean in raw_items:
            if len(item_clean) < 15:
                continue
            item_lines = [
                line_item.strip()
                for line_item in item_clean.split("\n")
                if line_item.strip()
            ]
            if not item_lines:
                continue

            title = item_lines[0]
            org = item_lines[1] if len(item_lines) > 1 else None
            if len(item_lines) > 2:
                content = " ".join(item_lines[2:])
            elif len(item_lines) == 2:
                content = item_lines[1]
            else:
                content = title

            item_full_text = " ".join(item_lines)
            lowered = item_full_text.lower()

            # Detect category
            cat = "experience"
            if any(t in lowered for t in HACKATHON_TRIGGERS):
                cat = "hackathon_achievement"
            elif any(t in lowered for t in OPEN_SOURCE_TRIGGERS):
                cat = "open_source"

            item_skills = extract_skills_from_text(item_full_text)
            item_metrics = extract_metrics(item_full_text)
            star = synthesize_star_breakdown(content, item_skills, item_metrics)

            is_quant = bool(item_metrics) or cat == "hackathon_achievement"

            blocks.append(
                ParsedCVBlock(
                    category=cat,
                    title=title,
                    organization=org,
                    content=content,
                    star_breakdown=star,
                    metrics=item_metrics,
                    skills=item_skills,
                    is_quantified=is_quant,
                )
            )

    # Fallback all skills
    all_skills = list(set(skills_list + extract_skills_from_text(text)))

    return ParsedCandidateData(
        full_name=full_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        headline=headline,
        detected_format="linkedin_pdf",
        skills=sorted(all_skills),
        blocks=blocks,
        raw_text=text[:10000],
    )


def parse_generic_resume_text(text: str) -> ParsedCandidateData:
    """
    Parse generic PDF, Word, or plain text resume layout.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    full_name = "Candidate"
    email = None
    phone = None
    linkedin_url = None
    github_url = None

    # Contact info
    emails = RE_EMAIL.findall(text)
    if emails:
        email = emails[0]
    phones = RE_PHONE.findall(text)
    if phones:
        phone = phones[0]
    li = RE_LINKEDIN.findall(text)
    if li:
        linkedin_url = f"https://www.linkedin.com/in/{li[0]}"
    gh = RE_GITHUB.findall(text)
    if gh:
        github_url = f"https://github.com/{gh[0]}"

    # Resolve candidate name from first few lines
    for line in lines[:8]:
        if (
            "@" not in line
            and "http" not in line
            and len(line.split()) in [2, 3, 4]
            and not any(char.isdigit() for char in line)
            and line.lower() not in {"resume", "curriculum vitae", "cv"}
        ):
            full_name = line
            break

    # Section-based partitioning
    section_patterns = re.compile(
        r"^(?:#+\s*)?(experience|work\s+experience|projects|hackathons|competitions|"
        r"open\s+source|education|skills|technical\s+skills)\b",
        re.IGNORECASE,
    )

    current_section = "summary"
    sections: dict[str, list[str]] = {
        "summary": [],
        "experience": [],
        "projects": [],
        "hackathons": [],
        "education": [],
        "skills": [],
    }

    for line in lines:
        match = section_patterns.match(line)
        if match:
            header_token = match.group(1).lower()
            if "experience" in header_token:
                current_section = "experience"
            elif "project" in header_token:
                current_section = "projects"
            elif any(k in header_token for k in ["hackathon", "competition"]):
                current_section = "hackathons"
            elif "education" in header_token:
                current_section = "education"
            elif "skill" in header_token:
                current_section = "skills"
            continue
        sections[current_section].append(line)

    blocks: list[ParsedCVBlock] = []

    # Process experience & projects & hackathons
    for sec_name, sec_lines in sections.items():
        if sec_name in ["summary", "skills"] or not sec_lines:
            continue

        sec_text = "\n".join(sec_lines)
        # Split on bullet points or role headers
        bullet_items = re.split(r"\n(?=[•\-\*]|\d+\.\s+)", sec_text)
        for b_item in bullet_items:
            clean_b = b_item.strip(" •-*")
            if len(clean_b) < 15:
                continue

            lowered = clean_b.lower()
            if sec_name == "hackathons" or any(
                t in lowered for t in HACKATHON_TRIGGERS
            ):
                cat = "hackathon_achievement"
            elif any(t in lowered for t in OPEN_SOURCE_TRIGGERS):
                cat = "open_source"
            elif sec_name == "education" or any(
                t in lowered for t in EDUCATION_TRIGGERS
            ):
                cat = "education"
            elif sec_name == "projects":
                cat = "project"
            else:
                cat = "experience"

            b_skills = extract_skills_from_text(clean_b)
            b_metrics = extract_metrics(clean_b)
            star = synthesize_star_breakdown(clean_b, b_skills, b_metrics)

            title_sample = clean_b.split(".")[0][:60]

            blocks.append(
                ParsedCVBlock(
                    category=cat,
                    title=title_sample,
                    organization=None,
                    content=clean_b,
                    star_breakdown=star,
                    metrics=b_metrics,
                    skills=b_skills,
                    is_quantified=bool(b_metrics),
                )
            )

    all_skills = extract_skills_from_text(text)

    return ParsedCandidateData(
        full_name=full_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        detected_format="standard_resume",
        skills=all_skills,
        blocks=blocks,
        raw_text=text[:10000],
    )


def parse_resume_bytes(file_bytes: bytes, filename: str) -> ParsedCandidateData:
    """
    Dispatch file bytes to appropriate extraction parser based on filename extension.
    """
    lower_fn = filename.lower()
    if lower_fn.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_bytes)
        if detect_is_linkedin_pdf(raw_text):
            return parse_linkedin_text(raw_text)
        return parse_generic_resume_text(raw_text)
    elif lower_fn.endswith(".docx"):
        raw_text = extract_text_from_docx(file_bytes)
        return parse_generic_resume_text(raw_text)
    else:
        # Default plain text
        raw_text = file_bytes.decode("utf-8", errors="replace")
        if detect_is_linkedin_pdf(raw_text):
            return parse_linkedin_text(raw_text)
        return parse_generic_resume_text(raw_text)
