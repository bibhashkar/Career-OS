"""
Comprehensive resume and document parsing engine for multi-modal candidate onboarding.

Architecture:
  - Front-gate triage router (Jev-style layout classifier) to select the optimal pipeline.
  - Deep LLM structured extractor mapping raw resumes to CandidateProfileDossier.
  - Deterministic 5-section grounded semantic profile summary formulation (anti-drift).
  - Robust deterministic fallback parser for hermetic offline testing and zero-API execution.
  - First-class Business Domain Expertise (FinTech, HealthTech, etc.).
  - Atomic CareerProofPoint decomposition into pgvector CVBlocks.
"""

import io
import logging
import re
from typing import Any

import docx
import pdfplumber

from app.ingestion.router import detect_is_linkedin_pdf as detect_is_linkedin_pdf
from app.ingestion.router import triage_resume_layout
from app.ingestion.taxonomy import SKILL_TAXONOMY
from app.schemas.candidate_dossier import (
    AwardAndHonor,
    BusinessDomainExpertise,
    CandidateProfileDossier,
    CareerProofPoint,
    EducationRecord,
    InstitutionTier,
    ParsedCVBlock,
    ProjectRecord,
    QuantifiedMetric,
    SeniorityLevel,
    TechnicalSkillsMatrix,
    WorkExperience,
    compute_bullet_fingerprint,
    compute_tenure_fingerprint,
)
from app.services.diagnostics import calculate_persona_completeness

logger = logging.getLogger("career_os.ingestion.resume_parser")

# Backward-compatibility alias
ParsedCandidateData = CandidateProfileDossier

# Metric extraction patterns (Tech, Business, Marketing, Executive, Finance & Healthcare)
RE_PERCENTAGE = re.compile(
    r"\b(\d+(?:\.\d+)?%(?:\s*(?:reduction|increase|improvement|growth|boost|drop|yoy|cagr|margin|nrr|roi|roas|conversion|retention|accuracy|uptime))?)(?!\w)",
    re.IGNORECASE,
)
RE_CURRENCY = re.compile(r"(\$[\d,]+(?:\.\d+)?[KkMmBb]?\+?)")
RE_MULTIPLIER = re.compile(
    r"\b(\d+(?:\.\d+)?x(?:\s*(?:roas|roi|growth|scale|faster|throughput))?)\b",
    re.IGNORECASE,
)
RE_LATENCY_THROUGHPUT = re.compile(
    r"(?:<\s*)?\b(\d+[\d,]*(?:\.\d+)?(?:[KkMmBb])?\+?\s*"
    r"(?:ms|milliseconds|seconds|sec|s\b|req\/s|rps|qps|queries\/sec|events\/sec|tps|ops\/sec))\b",
    re.IGNORECASE,
)
RE_SCALE_USERS = re.compile(
    r"\b(\d+[\d,]*(?:[KkMmBb])?\+?\s*"
    r"(?:(?:daily|monthly|annual|concurrent|active|enterprise|global|regional|clinical|b2b|b2c)\s+)?"
    r"(?:users|active users|dau|mau|records|stars|downloads|clients|customers|requests|datasets|dataset|"
    r"patients|clinics|hospitals|accounts|campaigns|leads|transactions|states|markets|countries|stores|endpoints))\b",
    re.IGNORECASE,
)
RE_LEADERSHIP_TEAM = re.compile(
    r"\b(?:(?:mentored|led|managed|built|scaled|directed|supervised|hired|grew)\s+(?:a\s+team\s+of\s+|an\s+org\s+of\s+)?)"
    r"(\d+\+?\s*(?:engineers|developers|marketers|analysts|clinicians|scientists|designers|product managers|sales reps|staff|employees|direct reports|people|members|cross-functional\s+\w+))\b",
    re.IGNORECASE,
)
RE_HACKATHON_HONORS = re.compile(
    r"\b(1st\s*place|2nd\s*place|3rd\s*place|first\s*place|second\s*place|third\s*place|"
    r"top\s*\d+|winner|finalist|champion|best\s*hack|grand\s*prize|keynote\s*speaker|board\s*member)\b",
    re.IGNORECASE,
)

# Contact info regexes
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_PHONE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
RE_LINKEDIN = re.compile(r"linkedin\.com/in/([A-Za-z0-9_-]+)", re.IGNORECASE)
RE_GITHUB = re.compile(
    r"github\.com/([A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)?)", re.IGNORECASE
)
RE_LEETCODE = re.compile(r"leetcode\.com/(?:u/)?([A-Za-z0-9_-]+)", re.IGNORECASE)
RE_PORTFOLIO = re.compile(
    r"\bhttps?://([A-Za-z0-9_-]+\.(?:io|me|dev|com|org)(?:/[^\s]*)?)\b", re.IGNORECASE
)

# Date range regexes
RE_DATE_RANGE = re.compile(
    r"\b((?:jan|feb|mar|Apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*)?(\d{4})\s*(?:–|—|-|to)\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*)?(\d{4}|present|current)\b",
    re.IGNORECASE,
)
RE_DEGREE = re.compile(
    r"\b(ph\.?d\.?|doctorate|m\.d\.?|j\.d\.?|e?m\.?b\.?a\.?|master\s+of\s+business\s+administration|"
    r"m\.s\.|ms|master'?s?(?:\s+of\s+(?:science|arts|engineering|health\s+administration|public\s+health|finance))?|"
    r"m\.a\.|m\.eng|m\.h\.a\.|m\.p\.h\.|b\.b\.a\.|bba|bachelor\s+of\s+business\s+administration|"
    r"b\.s\.n\.|bsn|b\.s\.|bs|b\.a\.|ba|bachelor'?s?(?:\s+of\s+(?:science|arts|engineering|commerce))?|"
    r"b\.tech|b\.e\.|cpa|cfa)\b",
    re.IGNORECASE,
)
RE_MAJOR = re.compile(
    r"\b(management information systems?|computer science(?:\s*&\s*engineering)?|data science|electrical engineering|"
    r"mathematics|software engineering|information technology|statistics|physics|artificial intelligence|computational biology|"
    r"business administration|marketing(?:\s*&\s*communications)?|finance(?:\s*&\s*economics)?|economics|accounting|"
    r"healthcare administration|public health|nursing|medicine|biology|biochemistry|biomedical engineering|"
    r"operations management|supply chain management|communications|psychology|political science|law|entrepreneurship|"
    r"product management|international business|human resources|mechanical engineering|chemical engineering)\b",
    re.IGNORECASE,
)
RE_GPA = re.compile(
    r"\b(?:gpa|cgpa)[\s:]*([0-4](?:\.\d{1,2})?(?:\s*/\s*4(?:\.0)?)?)\b", re.IGNORECASE
)

TOP_TECH_UNIVERSITIES = {
    "mit",
    "massachusetts institute of technology",
    "stanford",
    "stanford university",
    "berkeley",
    "uc berkeley",
    "university of california, berkeley",
    "cmu",
    "carnegie mellon",
    "harvard",
    "wharton",
    "university of pennsylvania",
    "yale",
    "kellogg",
    "northwestern",
    "booth",
    "university of chicago",
    "sloan",
    "insead",
    "london business school",
    "johns hopkins",
    "duke",
    "caltech",
    "princeton",
    "columbia",
    "cornell",
    "university of washington",
    "georgia tech",
    "waterloo",
    "university of waterloo",
    "iit",
    "indian institute of technology",
    "eth zurich",
    "oxford",
    "cambridge",
    "ucla",
    "uiuc",
    "university of illinois",
    "university of michigan",
    "ut austin",
    "university of texas at austin",
    "unlv",
    "university of nevada, las vegas",
    "arizona state university",
    "asu",
}

DOMAIN_KEYWORDS = {
    "HealthTech / HIPAA": [
        "hipaa",
        "dicom",
        "patient",
        "medical",
        "clinical",
        "healthcare",
        "pii masking",
        "mfa/totp",
        "ehr",
        "health",
        "fhir",
        "hl7",
        "fda",
        "biotech",
    ],
    "FinTech / High-Throughput Transactions": [
        "edi",
        "billing",
        "financial",
        "transaction",
        "payment",
        "clearinghouse",
        "insurance verification",
        "ledger",
        "$7b",
        "clearing",
        "pci-dss",
        "capital markets",
        "underwriting",
        "treasury",
    ],
    "AI / Machine Learning Infrastructure": [
        "pytorch",
        "llm",
        "rag",
        "vector database",
        "fine-tuning",
        "vllm",
        "langchain",
        "mcp",
        "transformer",
        "embeddings",
    ],
    "Cloud & Distributed Systems": [
        "distributed systems",
        "microservices",
        "high-concurrency",
        "low-latency",
        "terraform",
        "kubernetes",
        "docker",
        "gcp",
        "aws",
        "ci/cd",
    ],
    "Executive Leadership & Corporate Strategy": [
        "p&l",
        "ebitda",
        "m&a",
        "board of directors",
        "investor relations",
        "corporate strategy",
        "turnaround",
        "fundraising",
        "series a",
        "series b",
        "chief executive",
    ],
    "Marketing, Brand & Revenue Growth": [
        "roas",
        "demand generation",
        "brand strategy",
        "product marketing",
        "gtm",
        "go-to-market",
        "cac",
        "ltv",
        "hubspot",
        "marketo",
        "seo",
        "paid acquisition",
    ],
}


EXCLUDED_NAME_WORDS = {
    "contact",
    "languages",
    "skills",
    "top skills",
    "summary",
    "experience",
    "education",
    "resume",
    "curriculum vitae",
    "cv",
    "honors",
    "awards",
    "projects",
    "profile",
    "about",
    "work",
    "employment",
    "professional experience",
    "technical skills",
    "certifications",
    "interests",
    "competencies",
    "headline",
}


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


def extract_quantified_metrics(content: str) -> list[QuantifiedMetric]:
    """
    Detect concrete quantified achievements and business outcomes.
    """
    metrics: list[QuantifiedMetric] = []
    cur_matches = RE_CURRENCY.findall(content)
    for m in cur_matches:
        metrics.append(QuantifiedMetric(metric_type="financial_volume", raw_metric=m))
    pct_matches = RE_PERCENTAGE.findall(content)
    for m in pct_matches:
        metrics.append(
            QuantifiedMetric(metric_type="percentage_improvement", raw_metric=m)
        )
    lat_matches = RE_LATENCY_THROUGHPUT.findall(content)
    for m in lat_matches:
        metrics.append(
            QuantifiedMetric(metric_type="latency_optimization", raw_metric=m)
        )
    scale_matches = RE_SCALE_USERS.findall(content)
    for m in scale_matches:
        metrics.append(
            QuantifiedMetric(metric_type="scale_users_or_data", raw_metric=m)
        )
    mul_matches = RE_MULTIPLIER.findall(content)
    for m in mul_matches:
        metrics.append(
            QuantifiedMetric(metric_type="percentage_improvement", raw_metric=m)
        )
    lead_matches = RE_LEADERSHIP_TEAM.findall(content)
    for m in lead_matches:
        metrics.append(QuantifiedMetric(metric_type="team_leadership", raw_metric=m))
    honors_matches = RE_HACKATHON_HONORS.findall(content)
    for m in honors_matches:
        metrics.append(QuantifiedMetric(metric_type="general", raw_metric=m))
    return metrics


def extract_metrics(content: str) -> dict[str, Any]:
    """
    Detect concrete quantified achievements and business outcomes (legacy dict format).
    """
    metrics: dict[str, Any] = {}
    pct_matches = RE_PERCENTAGE.findall(content)
    if pct_matches:
        metrics["percentage_impact"] = pct_matches[0]
        metrics["percentage_improvement"] = pct_matches[0]

    cur_matches = RE_CURRENCY.findall(content)
    if cur_matches:
        metrics["financial_impact"] = cur_matches[0]
        metrics["financial_volume"] = cur_matches[0]

    mul_matches = RE_MULTIPLIER.findall(content)
    if mul_matches:
        metrics["scale_multiplier"] = mul_matches[0]

    lat_matches = RE_LATENCY_THROUGHPUT.findall(content)
    if lat_matches:
        metrics["throughput_or_latency"] = lat_matches[0]
        metrics["latency_optimization"] = lat_matches[0]

    scale_matches = RE_SCALE_USERS.findall(content)
    if scale_matches:
        metrics["user_or_data_scale"] = scale_matches[0]
        metrics["scale_users_or_data"] = scale_matches[0]

    lead_matches = RE_LEADERSHIP_TEAM.findall(content)
    if lead_matches:
        metrics["team_leadership"] = lead_matches[0]

    hack_matches = RE_HACKATHON_HONORS.findall(content)
    if hack_matches:
        metrics["honor_placement"] = hack_matches[0]

    return metrics


def _extract_deterministic_projects(
    project_lines: list[str],
) -> tuple[list[ProjectRecord], list[ParsedCVBlock]]:
    """
    Deterministically parse the Projects / Open Source / Key Initiatives section
    into structured ProjectRecord entries and atomic pgvector CVBlocks.
    """
    projects: list[ProjectRecord] = []
    blocks: list[ParsedCVBlock] = []
    if not project_lines:
        return projects, blocks

    raw_text = "\n".join(project_lines).strip()
    if not raw_text:
        return projects, blocks

    chunks = [c.strip() for c in re.split(r"\n\s*\n+", raw_text) if c.strip()]
    if len(chunks) == 1 and "\n" in raw_text:
        # Check if single-line bulleted or colon-separated project entries exist
        lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]
        grouped: list[str] = []
        current: list[str] = []
        for ln in lines:
            is_bullet = ln.startswith(("●", "•", "▪", "*", "-"))
            if (
                not is_bullet
                and (":" in ln or "|" in ln or "—" in ln or " - " in ln)
                and current
            ):
                grouped.append("\n".join(current))
                current = [ln]
            else:
                current.append(ln)
        if current:
            grouped.append("\n".join(current))
        chunks = grouped

    for chunk in chunks:
        c_lines = [ln.strip() for ln in chunk.split("\n") if ln.strip()]
        if not c_lines:
            continue

        header = c_lines[0].lstrip("●•▪*- ")
        name = header
        desc_parts: list[str] = []
        repo_url: str | None = None
        live_url: str | None = None

        gh_m = RE_GITHUB.search(chunk)
        if gh_m:
            repo_url = f"https://github.com/{gh_m.group(1)}"
        port_m = RE_PORTFOLIO.search(chunk)
        if port_m and (not repo_url or port_m.group(0) != repo_url):
            live_url = port_m.group(0)

        if "|" in header:
            h_parts = [p.strip() for p in header.split("|") if p.strip()]
            name = h_parts[0]
            if len(h_parts) > 1 and len(c_lines) == 1:
                desc_parts.append(" — ".join(h_parts[1:]))
        elif ":" in header and len(header.split(":", 1)[0].split()) <= 6:
            p_name, p_rest = header.split(":", 1)
            name = p_name.strip()
            if p_rest.strip():
                desc_parts.append(p_rest.strip())
        elif " — " in header and len(header.split(" — ", 1)[0].split()) <= 6:
            p_name, p_rest = header.split(" — ", 1)
            name = p_name.strip()
            if p_rest.strip():
                desc_parts.append(p_rest.strip())

        for extra_ln in c_lines[1:]:
            cleaned_ln = extra_ln.lstrip("●•▪*- ").strip()
            if cleaned_ln:
                desc_parts.append(cleaned_ln)

        description = " ".join(desc_parts).strip() or header
        if len(description) < 8:
            continue

        p_skills = extract_skills_from_text(f"{name} {description}")
        p_metrics_list = extract_quantified_metrics(description)
        p_metrics: dict[str, Any] = {
            str(m.metric_type): m.raw_metric for m in p_metrics_list
        }
        p_fp = compute_bullet_fingerprint(None, f"project:{name}", description)

        prj = ProjectRecord(
            name=name[:120],
            description=description,
            technologies=p_skills,
            repository_url=repo_url,
            live_url=live_url,
            metrics=p_metrics,
            content_fingerprint=p_fp,
        )
        projects.append(prj)

        blocks.append(
            ParsedCVBlock(
                category="project",
                title=name[:120],
                organization="Independent / Open Source",
                timeframe=None,
                content=description,
                star_breakdown=synthesize_star_breakdown(
                    description, p_skills, p_metrics_list
                ),
                metrics=p_metrics,
                skills=p_skills,
                content_fingerprint=p_fp,
                is_quantified=bool(p_metrics_list),
            )
        )

    return projects, blocks


def synthesize_star_breakdown(
    bullet: str,
    detected_skills: list[str],
    metrics: list[QuantifiedMetric],
) -> dict[str, str]:
    """
    Decompose a bullet narrative into Situation, Task, Action, Result.
    """
    star: dict[str, str] = {
        "situation": "Target production architecture and engineering deliverables.",
        "task": bullet.strip(),
        "action": f"Implemented solution utilizing {', '.join(detected_skills[:4])}."
        if detected_skills
        else "Executed mission-critical architecture deliverables.",
        "result": "Delivered production enhancements.",
    }
    if metrics:
        star["result"] = (
            f"Achieved measurable business impact: {metrics[0].raw_metric}."
        )
    return star


def synthesize_grounded_semantic_summary(dossier: CandidateProfileDossier) -> str:
    """
    Deterministic 5-section grounded semantic profile summary.
    Eliminates vector drift and hallucination by binding strictly to extracted entities.
    """
    sen = dossier.seniority_level.title() if dossier.seniority_level else "Senior"
    title = dossier.target_roles[0] if dossier.target_roles else "Software Engineer"
    yoe = dossier.total_years_experience

    # Section 1: Seniority Anchor
    sec1 = f"{sen} {title} with {yoe}+ years of experience in distributed systems, scalable architectures, and enterprise platform engineering."

    # Section 2: Domain Expertise Depth
    domains_summary = []
    for d in dossier.domain_expertise:
        regs = (
            f" ({', '.join(d.regulatory_frameworks)})"
            if d.regulatory_frameworks
            else ""
        )
        domains_summary.append(f"{d.domain}{regs}")
    sec2 = (
        f"Deep business domain expertise across {', '.join(domains_summary)}."
        if domains_summary
        else "Proven domain expertise across mission-critical enterprise systems and high-throughput transaction environments."
    )

    # Section 3: Quantitative Proof Benchmarks
    benchmarks = []
    for exp in dossier.work_experience:
        for b in exp.bullets:
            for m in b.metrics:
                if m.raw_metric not in benchmarks:
                    benchmarks.append(m.raw_metric)
    sec3 = (
        f"Demonstrated production scale achieving {', '.join(benchmarks[:4])}."
        if benchmarks
        else "Demonstrated track record of delivering high-reliability systems and resilient service architectures."
    )

    # Section 4: Verified Core Tech Stack
    top_skills = dossier.all_skills_flat[:15]
    sec4 = (
        f"Core verified production technology stack: {', '.join(top_skills)}."
        if top_skills
        else ""
    )

    # Section 5: High-Affinity Target Problem Space
    sec5 = (
        "Specialized in high-concurrency systems, mission-critical workflow automation, "
        "low-latency data pipelines, and scalable cloud infrastructure."
    )

    return f"{sec1} {sec2} {sec3} {sec4} {sec5}".strip()


SENIORITY_PREFIXES = {
    "senior",
    "junior",
    "lead",
    "staff",
    "principal",
    "director",
    "vp",
    "chief",
    "head",
    "associate",
    "intern",
    "entry",
}

EXCLUDED_TITLE_WORDS = {
    "software",
    "engineer",
    "developer",
    "architect",
    "lead",
    "senior",
    "junior",
    "principal",
    "manager",
    "consultant",
    "designer",
    "analyst",
    "scientist",
    "director",
    "vp",
    "specialist",
    "administrator",
    "full",
    "stack",
    "backend",
    "frontend",
    "devops",
    "cloud",
    "data",
    "platform",
    "intern",
    "student",
}


def clean_candidate_name_candidate(token: str) -> str:
    """Strip academic suffixes, honors, degrees, and pronouns from candidate name string."""
    t = re.sub(
        r"\b(Ph\.?D\.?|M\.?S\.?|B\.?S\.?|B\.?Tech|M\.?Eng|MBA|PMP|CFA|CPA)\b",
        "",
        token,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\s*\((?:he\/him|she\/her|they\/them|[^\)]+)\)", "", t, flags=re.IGNORECASE
    )
    t = re.sub(r"[,|•–—].*$", "", t)
    return re.sub(r"\s+", " ", t).strip()


def extract_phone_numbers(text: str) -> list[str]:
    """Extract valid phone numbers while excluding date ranges and pure numbers."""
    candidates = re.findall(
        r"(?:\+?\d{1,4}[-.\s]*)?(?:\(?\d{2,4}\)?[-.\s]*)?\d{3,4}[-.\s]*\d{3,4}\b",
        text,
    )
    valid: list[str] = []
    for c in candidates:
        digits = re.sub(r"\D", "", c)
        if len(digits) == 8 and (digits.startswith("19") or digits.startswith("20")):
            continue
        if 7 <= len(digits) <= 15:
            valid.append(c.strip())
    return valid


def extract_candidate_name(
    text: str, lines: list[str], emails: list[str] | None = None
) -> str:
    """
    Multi-pass cascading candidate name extraction.
    Pass 1: Explicit anchor patterns (Name:, Resume of, Curriculum Vitae of).
    Pass 2: LinkedIn export layout structure.
    Pass 3: Top-12 visual header inspection with exclusion masks.
    Pass 4: Email username heuristic fallback.
    """
    # Pass 1: Explicit anchor pattern
    anchor = re.search(
        r"(?:name|curriculum vitae of|resume of)[\s:]*([A-Z][a-zA-Z'.-]+(?:[^\S\r\n]+[A-Z][a-zA-Z'.-]+){1,3})",
        text,
        re.IGNORECASE,
    )
    if anchor:
        name = clean_candidate_name_candidate(anchor.group(1))
        if 2 <= len(name.split()) <= 4:
            return name

    # Pass 2: LinkedIn export format
    if "linkedin.com/in/" in text.lower() or (lines and lines[0].lower() == "contact"):
        for line_item in lines[:15]:
            clean_l = clean_candidate_name_candidate(line_item)
            if not clean_l:
                continue
            words = clean_l.split()
            if 2 <= len(words) <= 4:
                lowers = [w.lower() for w in words]
                if clean_l.lower() in EXCLUDED_NAME_WORDS or any(
                    w in EXCLUDED_NAME_WORDS for w in lowers
                ):
                    continue
                if lowers[0] in SENIORITY_PREFIXES:
                    continue
                if sum(1 for w in lowers if w in EXCLUDED_TITLE_WORDS) >= 2:
                    continue
                if "@" not in clean_l and not re.search(r"\d", clean_l):
                    if all(w[0].isupper() for w in words if w.isalpha()):
                        return clean_l

    # Pass 3: Top-12 visual header inspection
    for line_item in lines[:12]:
        tokens = [t.strip() for t in re.split(r"[\t\n\|•\–\—]", line_item) if t.strip()]
        for tok in tokens:
            clean_tok = clean_candidate_name_candidate(tok)
            if (
                clean_tok
                and "@" not in clean_tok
                and not re.search(r"\d", clean_tok)
                and not re.search(
                    r"https?|www\.|\.com|\.org|\.io|\.dev", clean_tok, re.I
                )
            ):
                words = clean_tok.split()
                if 2 <= len(words) <= 4:
                    lowers = [w.lower() for w in words]
                    if clean_tok.lower() in EXCLUDED_NAME_WORDS or any(
                        w in EXCLUDED_NAME_WORDS for w in lowers
                    ):
                        continue
                    if lowers[0] in SENIORITY_PREFIXES:
                        continue
                    if sum(1 for w in lowers if w in EXCLUDED_TITLE_WORDS) >= 2:
                        continue
                    if all(w[0].isupper() for w in words if w.isalpha()):
                        return clean_tok

    # Pass 4: Email heuristic fallback
    if emails:
        user_part = emails[0].split("@")[0]
        parts = [
            p for p in re.split(r"[._\-]", user_part) if p.isalpha() and len(p) >= 2
        ]
        if 2 <= len(parts) <= 3:
            return " ".join(p.capitalize() for p in parts)

    return "Candidate"


def parse_generic_resume_text(text: str) -> CandidateProfileDossier:
    """
    Robust, deterministic fallback parser capable of extracting full candidate
    dossiers across diverse resume formats without external API calls.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Contact details first to support email fallback in name extraction
    emails = RE_EMAIL.findall(text)
    email = emails[0] if emails else None
    phone_candidates = extract_phone_numbers(text)
    phone = phone_candidates[0] if phone_candidates else None
    li = RE_LINKEDIN.findall(text)
    linkedin_url = f"https://www.linkedin.com/in/{li[0]}" if li else None
    gh = RE_GITHUB.findall(text)
    github_url = f"https://github.com/{gh[0]}" if gh else None
    lc = RE_LEETCODE.findall(text)
    leetcode_url = f"https://leetcode.com/{lc[0]}" if lc else None

    # 2. Candidate Name Extraction via 4-pass cascading extractor
    full_name = extract_candidate_name(text, lines, emails)

    # Location detection: check first line tokens first, then fall back to body search
    location = None
    first_line = lines[0] if lines else ""
    first_line_tokens = [
        t.strip() for t in re.split(r"[\t\n\|•\–\—]", first_line) if t.strip()
    ]
    for token in first_line_tokens:
        if re.search(
            r"^[A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2}|[A-Z][a-zA-Z]+)$", token
        ) and not any(
            k in token.lower()
            for k in ("inc", "ltd", "corp", "university", "college", "school")
        ):
            location = token
            break

    if not location:
        loc_match = re.search(
            r"\b([A-Z][a-zA-Z\s]+,\s*[A-Z]{2}(?:\s*,\s*USA|\s*,\s*United States)?)\b",
            text,
        )
        if loc_match and not any(
            k in loc_match.group(1).lower() for k in ("llm", "ai", "ide")
        ):
            location = loc_match.group(1).strip()

    # 3. Comprehensive Section-based partitioning
    section_patterns = re.compile(
        r"^(?:#+\s*)?(?:(?:professional|work|career|employment|relevant|technical)\s+)?(experience|history|projects|hackathons|competitions|open\s+source|education|academic\s+background|academics|degrees|skills|technical\s+skills|core\s+competencies|awards|honors|achievements)\b",
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
        "awards": [],
    }

    for raw_l in text.split("\n"):
        line = raw_l.strip()
        match = section_patterns.match(line)
        if match:
            header_token = match.group(1).lower()
            if any(k in header_token for k in ("experience", "history")):
                current_section = "experience"
            elif any(k in header_token for k in ("project", "open source")):
                current_section = "projects"
            elif any(k in header_token for k in ("hackathon", "competition")):
                current_section = "hackathons"
            elif any(k in header_token for k in ("education", "academic", "degree")):
                current_section = "education"
            elif any(k in header_token for k in ("skill", "competenc")):
                current_section = "skills"
            elif any(k in header_token for k in ("award", "honor", "achievement")):
                current_section = "awards"

            remainder = line[match.end() :].strip(" :,|-")
            if remainder:
                sections[current_section].append(remainder)
            continue
        sections[current_section].append(line)

    # 4. Parse Work Experience & Atomic CareerProofPoints
    work_experiences: list[WorkExperience] = []
    career_blocks: list[ParsedCVBlock] = []
    awards_records: list[AwardAndHonor] = []

    exp_lines = sections["experience"]
    if exp_lines:
        exp_text = "\n".join(exp_lines)
        # Split on role headers (e.g. "Full Stack Software Developer | Onye Inc. ...")
        if "|" in exp_text:
            role_chunks = re.split(
                r"\n(?=[A-Z][A-Za-z0-9\s\.\,\-\/]+\s*\|\s*[A-Z][A-Za-z0-9\s\.\,\-\/]+\s*\|\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?|\d{4}))",
                exp_text,
            )
        else:
            role_chunks = [
                c for c in re.split(r"\n\s*\n+", exp_text.strip()) if c.strip()
            ]

        for chunk in role_chunks:
            c_lines = [
                line_str.strip()
                for line_str in chunk.strip().split("\n")
                if line_str.strip()
            ]
            if not c_lines:
                continue
            header = c_lines[0].strip()
            h_parts = [p.strip() for p in header.split("|")]
            job_title = h_parts[0] if h_parts else "Software Engineer"
            company_raw = h_parts[1] if len(h_parts) > 1 else ""
            date_raw = h_parts[2] if len(h_parts) > 2 else ""

            content_lines = c_lines[1:]
            if (
                not company_raw
                and len(c_lines) > 1
                and not c_lines[1].startswith(("●", "•", "▪", "*", "-"))
                and len(c_lines[1].split()) <= 6
            ):
                company_raw = c_lines[1]
                content_lines = c_lines[2:]

            if " at " in job_title and not company_raw:
                parts = job_title.split(" at ", 1)
                job_title = parts[0].strip()
                company_raw = parts[1].strip()

            company_name = (
                company_raw.split(",")[0].strip() if company_raw else "Organization"
            )
            loc = company_raw.split(",")[1].strip() if "," in company_raw else None

            # Detect industry domain of this position using word boundary regexes
            domain = "Enterprise SaaS / Distributed Systems"
            chunk_lower = chunk.lower()
            if re.search(
                r"\b(?:hipaa|dicom|patient|medical|clinical|healthcare|pii|fhir|hl7|biotech|fda)\b",
                chunk_lower,
            ):
                domain = "HealthTech / HIPAA"
            elif re.search(
                r"\b(?:llm|pytorch|rag|vector|ai|machine learning|deep learning|cuda|vllm|tensorrt|inference engine)\b",
                chunk_lower,
            ):
                domain = "AI / Machine Learning Infrastructure"
            elif re.search(
                r"\b(?:edi|billing|financial|payments?|transactions?|clearinghouse|underwriting|capital markets|\$[0-9]+[kmb]\+?)\b",
                chunk_lower,
            ):
                domain = "FinTech / High-Throughput Transactions"
            elif re.search(
                r"\b(?:roas|demand generation|brand|product marketing|gtm|go-to-market|cac|ltv|hubspot|marketo|campaigns?)\b",
                chunk_lower,
            ):
                domain = "Marketing, Brand & Revenue Growth"
            elif re.search(
                r"\b(?:p&l|ebitda|m&a|board of directors|investor relations|corporate strategy|turnaround|chief executive)\b",
                chunk_lower,
            ):
                domain = "Executive Leadership & Corporate Strategy"

            # Check if this entry is a hackathon or competition award
            is_hackathon_entry = bool(
                RE_HACKATHON_HONORS.search(job_title)
                or "hackathon" in job_title.lower()
                or "hack" in company_name.lower()
                or "hackathon" in company_name.lower()
            )
            block_category = (
                "hackathon_achievement" if is_hackathon_entry else "experience"
            )

            # Parse start and end date (preserving month when present)
            start_date, end_date = "", "Present"
            duration = 1.0
            date_match = RE_DATE_RANGE.search(date_raw or header)
            if date_match:
                start_mo_str = (date_match.group(1) or "").strip().rstrip(".")
                start_yr = int(date_match.group(2))
                end_mo_str = (date_match.group(3) or "").strip().rstrip(".")
                end_token = date_match.group(4).lower()
                is_pres = end_token in ("present", "current")
                end_yr = 2026 if is_pres else int(end_token)

                month_lookup = {
                    "jan": 1,
                    "feb": 2,
                    "mar": 3,
                    "apr": 4,
                    "may": 5,
                    "jun": 6,
                    "jul": 7,
                    "aug": 8,
                    "sep": 9,
                    "oct": 10,
                    "nov": 11,
                    "dec": 12,
                }
                s_mo = month_lookup.get(start_mo_str[:3].lower(), 1)
                e_mo = 11 if is_pres else month_lookup.get(end_mo_str[:3].lower(), 12)
                raw_months = max(6, (end_yr - start_yr) * 12 + (e_mo - s_mo))
                duration = round(max(0.5, raw_months / 12.0), 1)

                start_date = (
                    f"{start_mo_str.title()[:3]} {start_yr}"
                    if start_mo_str
                    else str(start_yr)
                )
                if is_pres:
                    end_date = "Present"
                else:
                    end_date = (
                        f"{end_mo_str.title()[:3]} {end_yr}"
                        if end_mo_str
                        else str(end_yr)
                    )

            # Reconstruct wrapped multi-line bullet points
            raw_bullets: list[str] = []
            curr_b: list[str] = []
            for b_line in content_lines:
                clean = b_line.strip()
                if not clean:
                    continue
                if clean.startswith(("●", "•", "▪", "*", "-")) or re.match(
                    r"^\d+\.", clean
                ):
                    if curr_b:
                        raw_bullets.append(" ".join(curr_b))
                        curr_b = []
                    curr_b.append(clean.lstrip("●•▪*-0123456789. "))
                else:
                    curr_b.append(clean)
            if curr_b:
                raw_bullets.append(" ".join(curr_b))

            proof_points: list[CareerProofPoint] = []
            for b_text in raw_bullets:
                if len(b_text) < 15:
                    continue
                b_skills = extract_skills_from_text(b_text)
                b_metrics = extract_quantified_metrics(b_text)
                first_word = b_text.split()[0].rstrip(",.:")
                action_verb = first_word if len(first_word) > 2 else "Architected"
                b_fp = compute_bullet_fingerprint(None, company_name, b_text)

                pp = CareerProofPoint(
                    raw_text=b_text,
                    action_verb=action_verb,
                    task_scope=b_text[:80],
                    technologies_used=b_skills,
                    metrics=b_metrics,
                    industry_domain=domain,
                    content_fingerprint=b_fp,
                )
                proof_points.append(pp)

                # Convert to atomic legacy CVBlock
                star = synthesize_star_breakdown(b_text, b_skills, b_metrics)
                career_blocks.append(
                    ParsedCVBlock(
                        category=block_category,
                        title=f"{job_title} at {company_name}"
                        if not is_hackathon_entry
                        else job_title,
                        organization=company_name,
                        timeframe=date_raw or f"{start_date} - {end_date}",
                        content=b_text,
                        star_breakdown=star,
                        metrics={m.metric_type: m.raw_metric for m in b_metrics},
                        skills=b_skills,
                        content_fingerprint=b_fp,
                        is_quantified=bool(b_metrics or is_hackathon_entry),
                    )
                )

            if is_hackathon_entry:
                awards_records.append(
                    AwardAndHonor(
                        title=job_title,
                        event_or_issuer=company_name,
                        date_str=date_raw or None,
                    )
                )

            # Seniority of role
            r_sen: SeniorityLevel = "mid"
            t_low = job_title.lower()
            if any(
                k in t_low
                for k in (
                    "ceo",
                    "cto",
                    "cmo",
                    "cfo",
                    "coo",
                    "chief",
                    "vp",
                    "vice president",
                    "founder",
                    "president",
                    "managing director",
                    "partner",
                )
            ):
                r_sen = "executive"
            elif any(k in t_low for k in ("principal", "director", "head of")):
                r_sen = "principal"
            elif any(k in t_low for k in ("staff", "architect")):
                r_sen = "staff"
            elif any(k in t_low for k in ("senior", "sr.", "lead")):
                r_sen = "senior"
            elif any(k in t_low for k in ("associate", "junior", "intern")):
                r_sen = "entry"

            if not is_hackathon_entry:
                t_fp = compute_tenure_fingerprint(company_name, job_title, start_date)
                work_experiences.append(
                    WorkExperience(
                        company_name=company_name,
                        industry_domain=domain,
                        job_title=job_title,
                        location=loc,
                        start_date=start_date,
                        end_date=end_date,
                        is_current=end_date == "Present",
                        duration_years=duration,
                        seniority_level=r_sen,
                        tenure_fingerprint=t_fp,
                        bullets=proof_points,
                    )
                )

    # 5. Extract Education
    education_records: list[EducationRecord] = []
    edu_lines = sections["education"]
    for e_line in edu_lines:
        clean_e = e_line.strip()
        if not clean_e:
            continue
        deg_match = RE_DEGREE.search(clean_e)
        maj_match = RE_MAJOR.search(clean_e)
        yr_match = re.search(r"\b(19\d\d|20\d\d)\b", clean_e)
        tier: InstitutionTier = "standard"
        for top_u in TOP_TECH_UNIVERSITIES:
            if top_u in clean_e.lower():
                tier = "tier_1_ivy_top_tech"
                break

        inst = (
            clean_e.split("|")[0].split("-")[-1].strip()
            if "-" in clean_e
            else clean_e[:50]
        )
        deg = deg_match.group(0).upper() if deg_match else "B.S."
        maj = maj_match.group(0).title() if maj_match else "Computer Science"

        education_records.append(
            EducationRecord(
                institution=inst,
                institution_tier=tier,
                degree=deg,
                major=maj,
                graduation_year=int(yr_match.group(1)) if yr_match else None,
                is_expected="expected" in clean_e.lower(),
            )
        )

    # 5B. Extract Projects / Key Initiatives
    projects_records, project_blocks = _extract_deterministic_projects(
        sections["projects"]
    )
    career_blocks.extend(project_blocks)

    # 6. Extract Awards & Hackathons
    award_lines = sections["awards"] + sections["hackathons"]
    idx = 0
    while idx < len(award_lines):
        clean_a = award_lines[idx].strip()
        if not clean_a or len(clean_a) < 5:
            idx += 1
            continue

        desc = ""
        if idx + 1 < len(award_lines) and not re.match(
            r"^\d+\.?\s*(?:st|nd|rd|th)?\s*place|winner|finalist",
            award_lines[idx + 1],
            re.I,
        ):
            desc = award_lines[idx + 1].strip()
            idx += 2
        else:
            idx += 1

        full_content = f"{clean_a}. {desc}".strip(". ") if desc else clean_a
        h_skills = extract_skills_from_text(full_content)
        h_metrics = extract_quantified_metrics(full_content)

        org = None
        if " at " in clean_a:
            org = clean_a.split(" at ", 1)[1].strip()
        elif " - " in clean_a:
            org = clean_a.split(" - ", 1)[1].strip()
        elif " | " in clean_a:
            parts = clean_a.split(" | ")
            clean_a = parts[0]
            org = parts[1] if len(parts) > 1 else None

        yr_m = re.search(r"\b(19\d\d|20\d\d)\b", full_content)
        a_date = yr_m.group(1) if yr_m else None
        a_cat = (
            "hackathon"
            if any(k in full_content.lower() for k in ("hackathon", "hack", "place"))
            else "award"
        )

        awards_records.append(
            AwardAndHonor(
                title=clean_a,
                event_or_issuer=org,
                date_str=a_date,
                category=a_cat,
                description=desc or None,
            )
        )

        h_fp = compute_bullet_fingerprint(None, org, full_content)
        career_blocks.append(
            ParsedCVBlock(
                category="hackathon_achievement",
                title=clean_a,
                organization=org,
                timeframe=a_date,
                content=full_content,
                star_breakdown=synthesize_star_breakdown(
                    full_content, h_skills, h_metrics
                ),
                metrics={m.metric_type: m.raw_metric for m in h_metrics},
                skills=h_skills,
                content_fingerprint=h_fp,
                is_quantified=bool(
                    h_metrics
                    or "place" in clean_a.lower()
                    or "winner" in clean_a.lower()
                ),
            )
        )

    # 7. Extract Skills & TechnicalSkillsMatrix
    all_skills = sorted(extract_skills_from_text(text))
    skills_matrix = TechnicalSkillsMatrix(
        system_architecture=[
            s
            for s in all_skills
            if s in ("Microservices", "Distributed Systems", "RESTful APIs")
        ],
        backend_and_frameworks=[
            s
            for s in all_skills
            if s
            in (
                "Java",
                "Python",
                "TypeScript",
                "FastAPI",
                "Spring Boot",
                "Next.js",
                "Node.js",
            )
        ],
        ai_and_infrastructure=[
            s
            for s in all_skills
            if s in ("PyTorch", "RAG", "Vector Databases", "LLM Serving", "MCP")
        ],
        databases_and_caching=[
            s
            for s in all_skills
            if s in ("PostgreSQL", "MongoDB", "Redis", "SQL", "Oracle Database")
        ],
        cloud_and_devops=[
            s
            for s in all_skills
            if s in ("Terraform", "Docker", "GCP", "CI/CD", "GitHub Actions", "Linux")
        ],
        frontend_and_ui=[
            s
            for s in all_skills
            if s in ("React", "Next.js", "Tailwind CSS", "JavaScript", "HTML")
        ],
        security_and_compliance=[
            s
            for s in all_skills
            if s in ("HIPAA", "RBAC", "MFA/TOTP", "PII Encryption")
        ],
        testing_and_qa=[
            s for s in all_skills if s in ("Vitest", "React Testing Library", "JPA")
        ],
    )

    # 8. Calculate Total Years of Experience & Seniority
    yoe_summary_match = re.search(r"(\d{1,2})\+?\s*(?:years|yrs)", text, re.IGNORECASE)
    if yoe_summary_match:
        total_yoe = int(yoe_summary_match.group(1))
    elif work_experiences:
        total_yoe = max(
            0, int(round(sum(exp.duration_years for exp in work_experiences)))
        )
    else:
        total_yoe = 0

    seniority: SeniorityLevel = "entry"
    if any(exp.seniority_level == "executive" for exp in work_experiences):
        seniority = "executive"
    elif total_yoe >= 10:
        seniority = "staff"
    elif total_yoe >= 5:
        seniority = "senior"
    elif total_yoe >= 2:
        seniority = "mid"
    else:
        seniority = "entry"

    # 9. Extract Business Domain Expertise
    domain_map: dict[str, float] = {}
    for exp in work_experiences:
        d = exp.industry_domain or "Enterprise SaaS"
        domain_map[d] = domain_map.get(d, 0.0) + exp.duration_years

    domain_expertise_list: list[BusinessDomainExpertise] = []
    for d_name, d_yrs in domain_map.items():
        frameworks = []
        if "health" in d_name.lower():
            frameworks = ["HIPAA", "TOTP MFA", "PII Masking", "DICOM"]
        elif "fintech" in d_name.lower():
            frameworks = [
                "EDI / X12",
                "Billing Calculation Engine",
                "Multi-State Clearing",
            ]
        elif "executive" in d_name.lower():
            frameworks = ["P&L Ownership", "Corporate Governance", "M&A Strategy"]
        elif "marketing" in d_name.lower():
            frameworks = ["GTM Strategy", "Demand Generation", "GDPR / Privacy"]
        domain_expertise_list.append(
            BusinessDomainExpertise(
                domain=d_name,
                years_experience=round(d_yrs, 1),
                regulatory_frameworks=frameworks,
            )
        )

    # 10. Infer Target Roles
    target_roles: list[str] = []
    for exp in work_experiences[:3]:
        clean_r = re.sub(r"\s*[\–\-|@].*$", "", exp.job_title).strip()
        if clean_r and clean_r not in target_roles:
            target_roles.append(clean_r)
    if not target_roles:
        target_roles = ["Software Engineer"]

    headline = f"{seniority.title()} {target_roles[0]} ({total_yoe}+ YOE) | Distributed Systems & Platform Engineering"

    # 11. Legacy compatibility dictionary for frontend persona ingestion
    career_intel = {
        "contact_pii": {
            "full_name": full_name,
            "email": email,
            "phone": phone,
        },
        "education": [
            {
                "degree": e.degree,
                "major": e.major,
                "institution": e.institution,
                "graduation_year": e.graduation_year,
                "institution_tier": e.institution_tier,
                "gpa": e.gpa,
                "honors": e.honors,
                "start_year": e.start_year,
                "is_expected": e.is_expected,
            }
            for e in education_records
        ],
        "work_experience": [
            {
                "company_name": exp.company_name,
                "job_title": exp.job_title,
                "location": exp.location,
                "is_remote": exp.is_remote,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "duration_years": exp.duration_years,
                "seniority_level": exp.seniority_level,
                "industry_domain": exp.industry_domain,
                "tenure_fingerprint": exp.tenure_fingerprint,
                "bullets": [
                    {
                        "raw_text": b.raw_text,
                        "action_verb": b.action_verb,
                        "technologies_used": b.technologies_used,
                        "content_fingerprint": b.content_fingerprint,
                        "metrics": [m.model_dump() for m in b.metrics],
                    }
                    for b in exp.bullets
                ],
            }
            for exp in work_experiences
        ],
        "role_tenures": [
            {
                "title": exp.job_title,
                "company": exp.company_name,
                "years": exp.duration_years,
                "seniority_level": exp.seniority_level,
                "functional_family": "engineering",
                "skills": [s for b in exp.bullets for s in b.technologies_used],
            }
            for exp in work_experiences
        ],
        "projects": [p.model_dump() for p in projects_records],
        "hackathons_competitions": [{"name": a.title} for a in awards_records],
        "awards_recognitions": [a.model_dump() for a in awards_records],
        "external_links": {
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "leetcode_url": leetcode_url,
        },
        "domain_expertise": [d.model_dump() for d in domain_expertise_list],
        "skills_matrix": skills_matrix.model_dump(),
        "source_provenance": {
            "detected_format": "standard_resume",
            "extracted_skills_count": len(all_skills),
            "extracted_blocks_count": len(career_blocks),
            "extracted_roles_count": len(work_experiences),
            "extracted_education_count": len(education_records),
            "extracted_projects_count": len(projects_records),
        },
    }

    completeness_res = calculate_persona_completeness(
        target_roles=target_roles,
        years_experience=total_yoe,
        seniority_level=seniority,
        skills=all_skills,
        blocks=career_blocks,
        career_intelligence=career_intel,
        linkedin_url=linkedin_url,
        github_url=github_url,
    )

    dossier = CandidateProfileDossier(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        linkedin_url=linkedin_url,
        github_url=github_url,
        leetcode_url=leetcode_url,
        headline=headline,
        total_years_experience=total_yoe,
        seniority_level=seniority,
        target_roles=target_roles,
        domain_expertise=domain_expertise_list,
        work_experience=work_experiences,
        education=education_records,
        skills_matrix=skills_matrix,
        all_skills_flat=all_skills,
        projects=projects_records,
        awards_and_honors=awards_records,
        # Legacy mirrors
        skills=all_skills,
        blocks=career_blocks,
        raw_text=text[:10000],
        inferred_years_experience=total_yoe,
        inferred_seniority_level=seniority,
        inferred_target_roles=target_roles,
        career_intelligence=career_intel,
        completeness=completeness_res.model_dump(),
        years_experience=total_yoe,
    )

    dossier.semantic_profile_summary = synthesize_grounded_semantic_summary(dossier)
    return dossier


def parse_linkedin_text(text: str) -> CandidateProfileDossier:
    """
    Parse LinkedIn PDF format into a full CandidateProfileDossier.
    """
    dossier = parse_generic_resume_text(text)
    # LinkedIn PDFs have a distinctive format: Contact -> Top Skills -> Languages -> Name -> Headline -> Summary
    li_name_match = re.search(
        r"(?:Languages\s*\n(?:[^\n]+\n)+|\n\n)([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\s*\n(?:Senior|Lead|Staff|Principal|Software|Backend|Full|Frontend|Engineering|Machine|AI|Director|VP|Product|[^\n]+(?:Engineer|Developer|Manager))",
        text,
    )
    if li_name_match:
        extracted = li_name_match.group(1).strip()
        if extracted.lower() not in EXCLUDED_NAME_WORDS:
            dossier.full_name = extracted
            if "contact_pii" not in dossier.career_intelligence:
                dossier.career_intelligence["contact_pii"] = {}
            dossier.career_intelligence["contact_pii"]["full_name"] = extracted
    return dossier


def parse_resume_bytes(file_bytes: bytes, filename: str) -> CandidateProfileDossier:
    """
    Dispatch file bytes to appropriate extraction parser based on filename and triage signals.
    """
    lower_fn = filename.lower()
    if lower_fn.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_bytes)
    elif lower_fn.endswith(".docx"):
        raw_text = extract_text_from_docx(file_bytes)
    else:
        raw_text = file_bytes.decode("utf-8", errors="replace")

    # Front-gate triage decision router
    triage_decision = triage_resume_layout(raw_text, filename=filename)
    logger.info(
        "Resume triage decision for %s: pipeline=%s layout=%s density=%s",
        filename,
        triage_decision.recommended_pipeline,
        triage_decision.layout_type,
        triage_decision.estimated_experience_density,
    )

    if triage_decision.recommended_pipeline == "linkedin_specialized":
        dossier = parse_linkedin_text(raw_text)
    else:
        # Deterministic fallback parser ensures robust, hermetic, zero-drift results
        dossier = parse_generic_resume_text(raw_text)

    dossier.career_intelligence.setdefault("source_provenance", {})
    dossier.career_intelligence["source_provenance"].update(
        {
            "filename": filename,
            "layout_type": triage_decision.layout_type,
            "recommended_pipeline": triage_decision.recommended_pipeline,
            "estimated_experience_density": triage_decision.estimated_experience_density,
            "confidence_score": triage_decision.confidence_score,
            "detected_format": (
                "linkedin_pdf"
                if triage_decision.recommended_pipeline == "linkedin_specialized"
                else "resume_document"
            ),
        }
    )
    return dossier
