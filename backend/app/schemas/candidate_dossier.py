"""
Pydantic domain models representing candidate resumes, granular proof points,
business domain expertise, and semantic matching profiles.
"""

import hashlib
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

LayoutType = Literal[
    "standard_single_column",
    "multi_column_creative",
    "linkedin_pdf_export",
    "academic_curriculum_vitae",
    "scanned_image_pdf",
    "plain_text",
]

RecommendedPipeline = Literal[
    "deep_llm_structured",
    "vision_ocr_pipeline",
    "linkedin_specialized",
    "deterministic_fallback",
]

ExperienceDensity = Literal["entry", "mid", "senior_staff", "executive"]

SeniorityLevel = Literal[
    "entry", "junior", "mid", "senior", "lead", "staff", "principal", "executive"
]

InstitutionTier = Literal["tier_1_ivy_top_tech", "tier_2_state_flagship", "standard"]

MetricType = Literal[
    "financial_volume",
    "throughput_or_traffic",
    "latency_optimization",
    "percentage_improvement",
    "scale_users_or_data",
    "team_leadership",
    "general",
]


def compute_bullet_fingerprint(user_id: str | None, org: str | None, text: str) -> str:
    """Compute deterministic unique content fingerprint for a career achievement bullet."""
    norm_user = str(user_id or "").strip().lower()
    norm_org = re.sub(r"[^a-z0-9]", "", str(org or "").lower())
    clean_text = re.sub(r"^[•\-*–\d.)\s]+", "", text.strip())
    norm_content = re.sub(r"\s+", " ", clean_text.lower()).strip()
    raw = f"{norm_user}:{norm_org}:{norm_content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def compute_tenure_fingerprint(company: str, title: str, start_year: str) -> str:
    """Compute deterministic unique fingerprint for an employment tenure."""
    norm_company = re.sub(r"[^a-z0-9]", "", company.lower())
    norm_company = re.sub(r"(inc|llc|ltd|corp|co|gmbh|sa)$", "", norm_company)
    norm_title = re.sub(r"[^a-z0-9]", "", title.lower())
    match_year = re.search(r"\b(19\d{2}|20\d{2})\b", str(start_year))
    norm_year = match_year.group(1) if match_year else "any"
    raw = f"{norm_company}:{norm_title}:{norm_year}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class QuantifiedMetric(BaseModel):
    """
    Concrete quantified metric demonstrating measurable impact.
    """

    metric_type: MetricType = "general"
    raw_metric: str
    impact_description: str = ""


class CareerProofPoint(BaseModel):
    """
    Atomic career accomplishment unit representing a single bullet point.
    Directly maps to a pgvector CVBlock for zero-hallucination tailoring.
    """

    raw_text: str
    action_verb: str = "Executed"
    task_scope: str = ""
    technologies_used: list[str] = Field(default_factory=list)
    metrics: list[QuantifiedMetric] = Field(default_factory=list)
    industry_domain: str | None = None
    content_fingerprint: str | None = None
    star_situation: str | None = None
    star_task: str | None = None
    star_action: str | None = None
    star_result: str | None = None


class WorkExperience(BaseModel):
    """
    Structured employment tenure at a single organization.
    """

    company_name: str
    industry_domain: str | None = None  # e.g. "HealthTech", "FinTech / Transactions"
    job_title: str
    location: str | None = None
    is_remote: bool = False
    start_date: str = ""
    end_date: str = "Present"
    is_current: bool = False
    duration_years: float = 1.0
    seniority_level: SeniorityLevel = "mid"
    tenure_fingerprint: str | None = None
    bullets: list[CareerProofPoint] = Field(default_factory=list)


class BusinessDomainExpertise(BaseModel):
    """
    First-class representation of industry business domain expertise (FinTech, HealthTech, etc.).
    Crucial for matching job requirements demanding specific industry background.
    """

    domain: str  # e.g. "FinTech", "HealthTech", "E-Commerce", "Enterprise SaaS"
    years_experience: float = 0.0
    regulatory_frameworks: list[str] = Field(
        default_factory=list
    )  # e.g. ["HIPAA", "EDI/X12", "PCI-DSS"]
    core_competencies: list[str] = Field(default_factory=list)
    evidence_proof_points: list[str] = Field(default_factory=list)


class EducationRecord(BaseModel):
    """
    Academic credential, institution, and achievement record.
    """

    institution: str
    institution_tier: InstitutionTier = "standard"
    degree: str  # e.g. "Master of Science", "Bachelor of Science"
    major: str  # e.g. "Computer Science & Engineering"
    minor: str | None = None
    start_year: int | None = None
    graduation_year: int | None = None
    is_expected: bool = False
    gpa: str | None = None
    honors: str | None = None
    relevant_coursework: list[str] = Field(default_factory=list)


class TechnicalSkillsMatrix(BaseModel):
    """
    Categorized technical competency profile.
    """

    system_architecture: list[str] = Field(default_factory=list)
    backend_and_frameworks: list[str] = Field(default_factory=list)
    ai_and_infrastructure: list[str] = Field(default_factory=list)
    databases_and_caching: list[str] = Field(default_factory=list)
    cloud_and_devops: list[str] = Field(default_factory=list)
    frontend_and_ui: list[str] = Field(default_factory=list)
    security_and_compliance: list[str] = Field(default_factory=list)
    testing_and_qa: list[str] = Field(default_factory=list)


class ProjectRecord(BaseModel):
    """
    Independent technical project or open-source initiative.
    """

    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    repository_url: str | None = None
    live_url: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class AwardAndHonor(BaseModel):
    """
    Competitive award, hackathon placement, or industry honor.
    """

    title: str
    event_or_issuer: str | None = None
    date_str: str | None = None
    description: str | None = None


class ResumeTriageDecision(BaseModel):
    """
    Decision-native triage classification determining parsing strategy.
    """

    layout_type: LayoutType = "standard_single_column"
    recommended_pipeline: RecommendedPipeline = "deep_llm_structured"
    has_text_layer: bool = True
    is_multi_column: bool = False
    estimated_experience_density: ExperienceDensity = "mid"
    confidence_score: float = 1.0
    reasoning: str | None = None


class ParsedCVBlock(BaseModel):
    """
    Legacy and DB-compatible atomic CV achievement block.
    """

    category: str
    title: str
    organization: str | None = None
    timeframe: str | None = None
    content: str
    star_breakdown: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    content_fingerprint: str | None = None
    is_quantified: bool = False


class CandidateProfileDossier(BaseModel):
    """
    Master candidate profile dossier synthesized from resume text.
    Provides deep granular structures while maintaining backwards compatibility.
    """

    # 1. Contact & Identity
    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    leetcode_url: str | None = None

    # 2. Executive Synthesis
    headline: str = ""
    total_years_experience: int = 0
    seniority_level: SeniorityLevel = "entry"
    target_roles: list[str] = Field(default_factory=list)

    # 3. Business & Industry Domain Depth
    domain_expertise: list[BusinessDomainExpertise] = Field(default_factory=list)

    # 4. Dense Semantic Profile Summary (Embedding-Engineered)
    semantic_profile_summary: str = ""

    # 5. Granular Records
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[EducationRecord] = Field(default_factory=list)
    skills_matrix: TechnicalSkillsMatrix = Field(default_factory=TechnicalSkillsMatrix)
    all_skills_flat: list[str] = Field(default_factory=list)
    projects: list[ProjectRecord] = Field(default_factory=list)
    awards_and_honors: list[AwardAndHonor] = Field(default_factory=list)

    # 6. Backwards-compatibility and frontend contract mirrors
    detected_format: str = "standard_resume"
    skills: list[str] = Field(default_factory=list)
    blocks: list[ParsedCVBlock] = Field(default_factory=list)
    raw_text: str = ""
    inferred_years_experience: int = 0
    inferred_seniority_level: str = "entry"
    inferred_target_roles: list[str] = Field(default_factory=list)
    career_intelligence: dict[str, Any] = Field(default_factory=dict)
    completeness: dict[str, Any] = Field(default_factory=dict)
    years_experience: int = 0
