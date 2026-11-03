"""
Three-tier diagnostic engine for holistic candidate and job evaluations.

Implements the three diagnostic tiers planned in Career-OS:
  - Tier 0: Holistic Candidate 360° Audit (Market percentile, T-shaped radar,
    quantified impact ratio, career ceiling diagnosis, distinction badges).
  - Tier 1: Per-Job Diagnostic Breakdown (Match probability, dealbreakers,
    phrasing equivalents, gate explanations).
  - Tier 2: Persona Market Benchmarks (Top market skills gap from active catalog,
    actionable high-ROI upskilling recommendations).
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cv_block import CVBlock
from app.models.job_listing import JobListing
from app.models.user_account import (
    CandidatePersona,
    JobMatchCache,
    UserAccount,
)
from app.services.matching import (
    calculate_achievement_score,
    calculate_prestige_score,
    calculate_skill_overlap,
)

logger = logging.getLogger("career_os.services.diagnostics")


# ---------------------------------------------------------------------------
# Persona Completeness & Readiness Engine (ADR-009)
# ---------------------------------------------------------------------------
class PersonaCompletenessPillars(BaseModel):
    """Granular score breakdown across 7 candidate intelligence dimensions (0-100)."""

    role_trajectory: int = Field(
        ..., description="Role targets & per-role YoE (max 15)"
    )
    skills_inventory: int = Field(
        ..., description="Core, tool & domain skills (max 20)"
    )
    work_experience: int = Field(
        ..., description="Work history & quantified STAR impact (max 20)"
    )
    education: int = Field(
        ..., description="Education major/minor, degree, university tier (max 15)"
    )
    projects: int = Field(..., description="Projects & open source (max 10)")
    achievements: int = Field(
        ..., description="Hackathons, LeetCode, competitions, awards (max 10)"
    )
    external_logistics: int = Field(
        ..., description="LinkedIn/GitHub, work auth, salary/location (max 10)"
    )


class CompletenessMissingStep(BaseModel):
    """Actionable step guiding user on what to complete to reach 100% accuracy."""

    pillar: str
    weight: int
    title: str
    action_prompt: str
    why_it_matters: str
    action_key: str


class PersonaCompletenessResult(BaseModel):
    """Evaluated profile completeness score, readiness gate, and actionable checklist."""

    score: int
    is_profile_ready: bool
    pillars: PersonaCompletenessPillars
    missing_steps: list[CompletenessMissingStep]
    status_reason: str


def calculate_persona_completeness(
    target_roles: list[str] | None,
    years_experience: int | None,
    seniority_level: str | None,
    skills: list[str] | None,
    blocks: list[Any] | None,
    career_intelligence: dict[str, Any] | None,
    visa_status: str | None = None,
    preferred_locations: list[str] | None = None,
    min_salary: int | None = None,
    linkedin_url: str | None = None,
    github_url: str | None = None,
) -> PersonaCompletenessResult:
    """
    Deterministic 7-dimension profile completeness scoring engine (0-100%).

    Threshold Rules:
      - 0% completeness: profile_ready = False. Grounded mode locked.
      - >= 10% completeness: profile_ready = True. Grounded mode unlocked with honest telemetry.
    """
    target_roles = target_roles or []
    skills = skills or []
    blocks = blocks or []
    career_intel = career_intelligence or {}
    role_tenures = career_intel.get("role_tenures") or []
    work_experience = career_intel.get("work_experience") or []
    education = career_intel.get("education") or []
    projects = career_intel.get("projects") or []
    hackathons = career_intel.get("hackathons_competitions") or []
    awards = career_intel.get("awards_recognitions") or []
    ext_links = career_intel.get("external_links") or {}
    profile_cfg = career_intel.get("profile_config") or {}
    archetype = str(
        profile_cfg.get("career_archetype") or "technology_engineering"
    ).lower()

    missing_steps: list[CompletenessMissingStep] = []

    # 1. Role Trajectory & Per-Role YoE (Max 15%)
    role_score = 0
    if target_roles:
        role_score += 8
    if (years_experience and years_experience > 0) or (
        seniority_level and seniority_level != "mid"
    ):
        role_score += 4
    if role_tenures or work_experience:
        role_score += 3

    if role_score < 15:
        missing_steps.append(
            CompletenessMissingStep(
                pillar="role_trajectory",
                weight=15 - role_score,
                title="Target Roles & Per-Role Experience",
                action_prompt=f"+{15 - role_score}%: Add your target roles and experience duration per role.",
                why_it_matters="Distinguishes your exact years in each role (e.g. 3 yrs Senior SWE vs 1 yr QA) to prevent mismatched levels.",
                action_key="add_roles",
            )
        )

    # 2. Skills Inventory (Max 20%)
    skill_count = len(skills)
    skill_score = min(20, skill_count * 4)
    if skill_score < 20:
        needed = 5 - min(5, skill_count)
        missing_steps.append(
            CompletenessMissingStep(
                pillar="skills_inventory",
                weight=20 - skill_score,
                title="Core & Domain Competencies",
                action_prompt=f"+{20 - skill_score}%: Add {needed} more core, leadership, or domain skills.",
                why_it_matters="Powers exact and directional skill-graph matching against non-negotiable job dealbreakers.",
                action_key="add_skills",
            )
        )

    # 3. Work Experience & Quantified Impact (Max 20%)
    exp_score = 0
    exp_blocks = [
        b
        for b in blocks
        if getattr(b, "category", "") == "experience"
        or (isinstance(b, dict) and b.get("category") == "experience")
    ]
    total_exp_items = max(len(exp_blocks), len(role_tenures), len(work_experience))
    if total_exp_items >= 2:
        exp_score += 12
    elif total_exp_items == 1:
        exp_score += 6

    # Quantified metric detection across CVBlocks, work_experience bullets, and role_tenures
    has_quantified = False
    for b in blocks:
        metrics = (
            b.get("metrics") if isinstance(b, dict) else getattr(b, "metrics", {})
        ) or {}
        is_quant = (
            b.get("is_quantified")
            if isinstance(b, dict)
            else getattr(b, "is_quantified", False)
        )
        if metrics or is_quant:
            has_quantified = True
            break
        content = (
            b.get("content") if isinstance(b, dict) else getattr(b, "content", "")
        ) or ""
        if any(char in content for char in ("%", "$")) or any(
            unit in content.lower()
            for unit in (
                "ms",
                "users",
                "dau",
                "mau",
                "reduced",
                "increased",
                "requests",
                "mentored",
                "roas",
                "arr",
                "ebitda",
                "patients",
            )
        ):
            has_quantified = True
            break
    if not has_quantified:
        for w in work_experience:
            if not isinstance(w, dict):
                continue
            for bul in w.get("bullets") or []:
                if not isinstance(bul, dict):
                    continue
                if bul.get("metrics"):
                    has_quantified = True
                    break
                raw_t = str(bul.get("raw_text") or "")
                if any(char in raw_t for char in ("%", "$")) or any(
                    unit in raw_t.lower()
                    for unit in (
                        "ms",
                        "users",
                        "requests",
                        "mentored",
                        "roas",
                        "arr",
                        "ebitda",
                        "patients",
                    )
                ):
                    has_quantified = True
                    break
            if has_quantified:
                break
    if not has_quantified:
        for r in role_tenures:
            desc = r.get("description", "") if isinstance(r, dict) else ""
            if any(char in desc for char in ("%", "$")):
                has_quantified = True
                break

    if has_quantified:
        exp_score += 8

    if exp_score < 20:
        missing_steps.append(
            CompletenessMissingStep(
                pillar="work_experience",
                weight=20 - exp_score,
                title="Work History & Quantified Outcomes",
                action_prompt=f"+{20 - exp_score}%: Add work experience with quantified impact metrics (%, $, scale).",
                why_it_matters="Powers 1536-dim semantic matching and proves proven business impact to employers.",
                action_key="add_experience",
            )
        )

    # 4. Education Intelligence (Max 15%)
    edu_score = 0
    edu_blocks = [
        b
        for b in blocks
        if getattr(b, "category", "") == "education"
        or (isinstance(b, dict) and b.get("category") == "education")
    ]
    if education or edu_blocks:
        first_edu = education[0] if education and isinstance(education[0], dict) else {}
        if first_edu.get("degree") or edu_blocks:
            edu_score += 6
        if first_edu.get("major"):
            edu_score += 5
        if first_edu.get("institution") or (
            edu_blocks and getattr(edu_blocks[0], "organization", None)
        ):
            edu_score += 4
        if edu_score == 0 and (education or edu_blocks):
            edu_score = 15

    if edu_score < 15:
        missing_steps.append(
            CompletenessMissingStep(
                pillar="education",
                weight=15 - edu_score,
                title="Education & Academic Pedigree",
                action_prompt=f"+{15 - edu_score}%: Add your Degree, Major/Minor, and University name.",
                why_it_matters="Qualifies you for degree-gated positions and activates university prestige boosters.",
                action_key="add_education",
            )
        )

    # 5. Projects, Key Initiatives, Case Studies & Open Source (Max 10%)
    proj_score = 0
    proj_blocks = [
        b
        for b in blocks
        if getattr(b, "category", "")
        in ("project", "open_source", "initiative", "case_study")
        or (
            isinstance(b, dict)
            and b.get("category")
            in ("project", "open_source", "initiative", "case_study")
        )
    ]
    if projects or proj_blocks:
        proj_score = 10
    else:
        proj_title = "Technical Projects & Open Source"
        proj_prompt = (
            "+10%: Showcase 1+ key technical Projects or Open-Source contributions."
        )
        if archetype in ("executive_leadership", "finance_fintech", "product_strategy"):
            proj_title = "Strategic Mandates, Deals & Key Initiatives"
            proj_prompt = "+10%: Showcase 1+ flagship Strategic Initiatives, Deals, or Transformations."
        elif archetype == "marketing_growth":
            proj_title = "Flagship Campaigns, Launches & Case Studies"
            proj_prompt = "+10%: Showcase 1+ flagship GTM Campaigns, Brand Launches, or Case Studies."
        elif archetype == "healthcare_lifesciences":
            proj_title = "Clinical Programs, Trials & Initiatives"
            proj_prompt = "+10%: Showcase 1+ Clinical Programs, Quality Initiatives, or Research Trials."

        missing_steps.append(
            CompletenessMissingStep(
                pillar="projects",
                weight=10,
                title=proj_title,
                action_prompt=proj_prompt,
                why_it_matters="Demonstrates execution ownership for initiatives beyond standard role titles.",
                action_key="add_projects",
            )
        )

    # 6. Distinctions, Honors, Publications, Board Seats & Competitions (Max 10%)
    achieve_score = 0
    achieve_blocks = [
        b
        for b in blocks
        if getattr(b, "category", "")
        in ("hackathon_achievement", "award", "publication", "patent")
        or (
            isinstance(b, dict)
            and b.get("category")
            in ("hackathon_achievement", "award", "publication", "patent")
        )
    ]
    has_leetcode = bool(
        ext_links.get("leetcode_url")
        or ext_links.get("leetcode_stats")
        or ext_links.get("leetcode_solved")
    )
    if hackathons or awards or achieve_blocks or has_leetcode:
        achieve_score = 10
    else:
        ach_title = "Hackathons, LeetCode & Distinctions"
        ach_prompt = (
            "+10%: Add Hackathon wins, Awards, Patents, or Competition rankings."
        )
        if archetype in ("executive_leadership", "finance_fintech"):
            ach_title = "Board Seats, Keynotes & Executive Honors"
            ach_prompt = "+10%: Add Board Seats, Keynote Speaking, Advisory Roles, or Industry Awards."
        elif archetype == "marketing_growth":
            ach_title = "Industry Awards, Speaking & Publications"
            ach_prompt = "+10%: Add Marketing/Industry Awards, Keynotes, or Published Thought Leadership."
        elif archetype == "healthcare_lifesciences":
            ach_title = "Publications, Fellowships, Grants & Honors"
            ach_prompt = "+10%: Add Peer-Reviewed Publications, Grants, Certifications, or Clinical Honors."

        missing_steps.append(
            CompletenessMissingStep(
                pillar="achievements",
                weight=10,
                title=ach_title,
                action_prompt=ach_prompt,
                why_it_matters="Highlights your competitive distinction to boost match probability on high-bar teams.",
                action_key="add_achievements",
            )
        )

    # 7. External Profiles & Search Logistics (Max 10%)
    logistics_score = 0
    has_ext = bool(
        linkedin_url
        or github_url
        or ext_links.get("linkedin_url")
        or ext_links.get("github_url")
        or ext_links.get("portfolio_url")
        or ext_links.get("executive_bio_url")
        or ext_links.get("orcid_url")
    )
    if has_ext:
        logistics_score += 4
    if visa_status and visa_status.lower() not in ("none", "unknown", ""):
        logistics_score += 3
    if preferred_locations or (min_salary and min_salary > 0):
        logistics_score += 3

    if logistics_score < 10:
        missing_steps.append(
            CompletenessMissingStep(
                pillar="external_logistics",
                weight=10 - logistics_score,
                title="External Links & Search Constraints",
                action_prompt=f"+{10 - logistics_score}%: Add LinkedIn/Portfolio/GitHub links, work authorization, and salary floor.",
                why_it_matters="Prevents wasted applications by hard-filtering out roles incompatible with your visa, location, or salary.",
                action_key="add_logistics",
            )
        )

    has_capability_signals = (
        bool(skills)
        or bool(blocks)
        or bool(education)
        or bool(role_tenures)
        or bool(work_experience)
        or bool(projects)
        or bool(hackathons)
        or bool(awards)
    )

    if not has_capability_signals:
        total_score = 0
        role_score = 0
        skill_score = 0
        exp_score = 0
        edu_score = 0
        proj_score = 0
        achieve_score = 0
        logistics_score = 0
        is_ready = False
        reason = (
            "Because you haven't shared your skills or profile with us yet, we cannot "
            "calculate personalized match scores or show the best-matched jobs for your background. "
            "You are currently browsing in Explorer Mode. Upload your CV or add your skills to unlock "
            "personalized Grounded matching."
        )
    else:
        total_score = (
            role_score
            + skill_score
            + exp_score
            + edu_score
            + proj_score
            + achieve_score
            + logistics_score
        )
        total_score = min(100, max(0, total_score))
        is_ready = total_score >= 10

        if not is_ready:
            reason = (
                f"Your profile is {total_score}% complete. You need at least 10% completeness "
                "with verified capability signals to unlock Grounded matching."
            )
        elif total_score < 100:
            reason = (
                f"Your profile is {total_score}% complete. Grounded matching is active. Complete remaining "
                "dimensions to maximize match precision."
            )
        else:
            reason = (
                "Your profile is 100% complete with full candidate intelligence active."
            )

    return PersonaCompletenessResult(
        score=total_score,
        is_profile_ready=is_ready,
        pillars=PersonaCompletenessPillars(
            role_trajectory=role_score,
            skills_inventory=skill_score,
            work_experience=exp_score,
            education=edu_score,
            projects=proj_score,
            achievements=achieve_score,
            external_logistics=logistics_score,
        ),
        missing_steps=missing_steps,
        status_reason=reason,
    )


class CompetencyDomainScore(BaseModel):
    """Domain score for T-Shaped radar chart."""

    category: str
    score: int = Field(..., description="Proficiency level 0-100.")
    skill_count: int
    top_skills: list[str]


class DistinctionBadge(BaseModel):
    """Verified professional badge surfaced on candidate profile."""

    code: str
    title: str
    description: str
    icon: str
    verified: bool


class HolisticCandidateAudit(BaseModel):
    """Complete 360° evaluation of candidate career health and market position."""

    user_id: str
    candidate_name: str
    overall_health_score: int = Field(..., description="Overall health index (0-100).")
    market_percentile: int = Field(
        ..., description="Estimated talent tier (e.g. 88 = Top 12%)."
    )
    quantified_impact_ratio: float = Field(
        ..., description="Fraction of STAR blocks with verifiable metrics."
    )
    quantified_blocks_count: int
    total_blocks_count: int
    t_shaped_radar: list[CompetencyDomainScore]
    career_ceiling_diagnosis: dict[str, Any]
    distinction_badges: list[DistinctionBadge]


# ---------------------------------------------------------------------------
# Tier 1: Per-Job Diagnostic Schemas
# ---------------------------------------------------------------------------
class JobDiagnosticReport(BaseModel):
    """Comprehensive drilldown for a single job opportunity."""

    job_id: str
    persona_id: str
    match_score: float
    probability_band: str
    hard_gate_pass: bool
    visa_status_message: str
    matched_skills: list[str]
    missing_dealbreakers: list[str]
    phrasing_equivalents: list[dict[str, str]]
    next_step_action: str


# ---------------------------------------------------------------------------
# Tier 2: Persona Market Benchmark Schemas
# ---------------------------------------------------------------------------
class MarketSkillGapItem(BaseModel):
    """High-demand skill in the active catalog absent from persona profile."""

    skill: str
    market_demand_pct: int = Field(
        ..., description="% of target roles requiring skill."
    )
    unlocked_jobs_count: int


class PersonaBenchmarkReport(BaseModel):
    """Macro-level industry skill requirements analyzed across target catalog."""

    persona_id: str
    persona_name: str
    target_roles: list[str]
    analyzed_jobs_count: int
    top_market_skills: list[dict[str, Any]]
    top_skill_gaps: list[MarketSkillGapItem]
    upskilling_pathways: list[dict[str, str]]


# ---------------------------------------------------------------------------
# Diagnostic Logic Implementation
# ---------------------------------------------------------------------------
async def generate_holistic_audit(
    db: AsyncSession,
    user_account_id: uuid.UUID,
) -> HolisticCandidateAudit:
    """
    Generate Tier 0 holistic 360° candidate assessment.
    """
    # 1. Fetch UserAccount and all associated CVBlocks
    stmt = (
        select(UserAccount)
        .options(
            selectinload(UserAccount.cv_blocks),
            selectinload(UserAccount.personas).selectinload(CandidatePersona.skills),
        )
        .where(UserAccount.id == user_account_id)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account is None:
        raise ValueError(f"User account not found for id: {user_account_id}")

    blocks: list[CVBlock] = account.cv_blocks or []

    # 2. Quantified Impact Calculation
    total_blocks = len(blocks)
    quantified_blocks = sum(
        1
        for b in blocks
        if (
            b.metrics
            and any(
                k in b.metrics
                for k in [
                    "percentage_impact",
                    "financial_impact",
                    "throughput_or_latency",
                    "user_or_data_scale",
                    "honor_placement",
                    "placement",
                ]
            )
        )
    )
    quant_ratio = (
        round(quantified_blocks / total_blocks, 2) if total_blocks > 0 else 0.0
    )

    # 3. T-Shaped Competency Radar Breakdown
    all_skills: set[str] = set()
    for b in blocks:
        for s in b.skills or []:
            all_skills.add(s)
    for p in account.personas or []:
        for ps in p.skills or []:
            all_skills.add(ps.skill_name)

    # Map skills into core competency categories
    domain_mappings = {
        "Languages & Core": {"python", "go", "java", "typescript", "c++", "rust"},
        "Backend & Microservices": {
            "fastapi",
            "django",
            "spring boot",
            "grpc",
            "graphql",
            "kafka",
            "rabbitmq",
        },
        "Cloud & DevOps": {
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "terraform",
            "ci/cd",
        },
        "Data & Storage": {
            "postgresql",
            "redis",
            "mysql",
            "mongodb",
            "elasticsearch",
            "pgvector",
        },
        "AI Systems & Orchestration": {
            "langgraph",
            "langchain",
            "openai",
            "vllm",
            "pytorch",
            "ollama",
        },
    }

    t_radar: list[CompetencyDomainScore] = []
    for domain, keywords in domain_mappings.items():
        matched = [s for s in all_skills if s.lower() in keywords]
        count = len(matched)
        domain_score = min(100, count * 25)
        t_radar.append(
            CompetencyDomainScore(
                category=domain,
                score=domain_score,
                skill_count=count,
                top_skills=matched[:4],
            )
        )

    # 4. Prestige & Distinction Badges
    organizations = [b.organization for b in blocks if b.organization]
    prestige = calculate_prestige_score(organizations)
    achievements = calculate_achievement_score(blocks)

    badges: list[DistinctionBadge] = []
    # Hackathon badge
    has_hackathon = any("hackathon" in (b.category or "").lower() for b in blocks)
    badges.append(
        DistinctionBadge(
            code="hackathon_winner",
            title="Hackathon Competitor & Winner",
            description="Demonstrated rapid prototyping and competition honors.",
            icon="trophy",
            verified=has_hackathon or achievements >= 0.6,
        )
    )

    # Tier-1 Pedigree badge
    badges.append(
        DistinctionBadge(
            code="tier1_pedigree",
            title="Tier-1 Scaleup / FAANG Pedigree",
            description=(
                "Tenure at internationally recognized high-engineering bar firms."
            ),
            icon="star",
            verified=prestige >= 0.8,
        )
    )

    # Quantified Metric Master
    badges.append(
        DistinctionBadge(
            code="quantified_metrics",
            title="Quantified Impact High-Signal",
            description=(
                "Over 60% of achievements backed by verifiable business outcomes."
            ),
            icon="bar_chart",
            verified=quant_ratio >= 0.6,
        )
    )

    # Open Source Leadership
    has_oss = any(
        "open_source" in (b.category or "").lower()
        or (b.metrics or {}).get("github_stars", 0) > 100
        for b in blocks
    )
    badges.append(
        DistinctionBadge(
            code="open_source_author",
            title="Open-Source Contributor",
            description=(
                "Active maintainer or contributor to open-source developer tooling."
            ),
            icon="git_branch",
            verified=has_oss,
        )
    )

    # 5. Market Percentile & Overall Health
    base_percentile = 50
    if quant_ratio >= 0.7:
        base_percentile += 20
    elif quant_ratio >= 0.4:
        base_percentile += 10

    if prestige >= 0.8:
        base_percentile += 15
    if achievements >= 0.8:
        base_percentile += 10
    if len(all_skills) >= 8:
        base_percentile += 5

    percentile = min(98, base_percentile)
    overall_health = int((percentile * 0.6) + (quant_ratio * 40))

    # 6. Career Ceiling Diagnosis
    if quant_ratio < 0.5:
        ceiling_barrier = "Vague Achievement Bullet Points"
        ceiling_action = (
            "Over 50% of your career blocks describe responsibilities rather than "
            "verifiable business outcomes. Rewrite bullets using the STAR framework: "
            "Situation, Task, Action, and Quantified Result (e.g. latency reduced)."
        )
    elif len(organizations) < 2:
        ceiling_barrier = "Limited Proven Scope"
        ceiling_action = (
            "Expand your profile by adding competitive hackathons or open-source "
            "repositories to demonstrate independent architectural ownership."
        )
    else:
        ceiling_barrier = "Staff-Level Architectural Influence"
        ceiling_action = (
            "To unlock Principal/Staff level opportunities, emphasize multi-team "
            "influence, cloud cost reduction at scale, and cross-functional leadership."
        )

    career_diagnosis = {
        "current_tier": "Senior Engineer" if percentile >= 75 else "Mid-Level Engineer",
        "next_target_tier": "Staff / Lead Engineer"
        if percentile >= 75
        else "Senior Engineer",
        "primary_barrier": ceiling_barrier,
        "recommended_action": ceiling_action,
    }

    return HolisticCandidateAudit(
        user_id=str(account.id),
        candidate_name=account.full_name,
        overall_health_score=overall_health,
        market_percentile=percentile,
        quantified_impact_ratio=quant_ratio,
        quantified_blocks_count=quantified_blocks,
        total_blocks_count=total_blocks,
        t_shaped_radar=t_radar,
        career_ceiling_diagnosis=career_diagnosis,
        distinction_badges=badges,
    )


async def generate_job_diagnostic(
    db: AsyncSession,
    persona_id: uuid.UUID,
    job_id: uuid.UUID,
) -> JobDiagnosticReport:
    """
    Generate Tier 1 per-job match diagnostics and dealbreaker chip analysis.
    """
    # 1. Fetch persona and job listing
    persona_stmt = (
        select(CandidatePersona)
        .options(
            selectinload(CandidatePersona.skills),
            selectinload(CandidatePersona.user_account),
        )
        .where(CandidatePersona.id == persona_id)
    )
    job_stmt = select(JobListing).where(JobListing.id == job_id)

    persona_res = await db.execute(persona_stmt)
    persona = persona_res.scalar_one_or_none()

    job_res = await db.execute(job_stmt)
    job = job_res.scalar_one_or_none()

    if persona is None or job is None:
        raise ValueError("Candidate persona or job listing not found.")

    persona_skills = {s.skill_name for s in (persona.skills or [])}
    persona_skills_lower = {s.strip().lower() for s in persona_skills if s.strip()}
    reqs = job.ats_requirements or {}
    job_skills = reqs.get("hard_skills", [])
    if not job_skills:
        job_skills = [
            s
            for s in persona_skills
            if s.lower() in (job.raw_description or "").lower()
        ]

    # Calculate skill overlap and phrasing equivalents
    _, matched_s, missing_s, equivs = calculate_skill_overlap(
        persona_skills,
        job_skills,
        candidate_skills_lower=persona_skills_lower,
    )

    # Check cached match evaluation if available
    cache_stmt = select(JobMatchCache).where(
        JobMatchCache.persona_id == persona_id,
        JobMatchCache.job_listing_id == job_id,
    )
    cache_res = await db.execute(cache_stmt)
    cache_entry = cache_res.scalar_one_or_none()

    match_score = cache_entry.match_score if cache_entry else 0.70
    hard_gate_pass = cache_entry.hard_gate_pass if cache_entry else True

    if match_score >= 0.75:
        band = "high"
        next_step = "High probability match. Ready for tailored CV generation."
    elif match_score >= 0.50:
        band = "moderate"
        next_step = (
            f"Moderate match. Consider addressing missing skills: "
            f"{', '.join(missing_s[:2])}."
        )
    else:
        band = "low"
        next_step = "Low match probability due to major tech stack discrepancies."

    # Visa status explanation
    account = persona.user_account
    user_visa = (account.visa_status if account else "None").strip().lower()
    job_visa = (job.visa_sponsorship or "").strip().lower()

    if user_visa in {"h-1b", "f-1 opt", "requires_sponsorship"}:
        if job_visa == "no":
            visa_msg = "Disqualified: Employer explicitly does not sponsor visas."
        elif job_visa in {"yes", "transfer_only", "opt_cpt_accepted"}:
            visa_msg = "Verified: Employer actively sponsors work visas."
        else:
            visa_msg = (
                "Unconfirmed: Visa sponsorship unstated. Bayesian discount applied."
            )
    else:
        visa_msg = "Domestic work authorization; visa gate fully satisfied."

    return JobDiagnosticReport(
        job_id=str(job.id),
        persona_id=str(persona.id),
        match_score=round(match_score, 2),
        probability_band=band,
        hard_gate_pass=hard_gate_pass,
        visa_status_message=visa_msg,
        matched_skills=matched_s[:6],
        missing_dealbreakers=missing_s[:4],
        phrasing_equivalents=equivs[:3],
        next_step_action=next_step,
    )


async def generate_persona_market_benchmark(
    db: AsyncSession,
    persona_id: uuid.UUID,
) -> PersonaBenchmarkReport:
    """
    Generate Tier 2 macro-level industry skill requirements analyzed
    across target catalog.
    """
    # 1. Fetch persona
    persona_stmt = (
        select(CandidatePersona)
        .options(selectinload(CandidatePersona.skills))
        .where(CandidatePersona.id == persona_id)
    )
    persona_res = await db.execute(persona_stmt)
    persona = persona_res.scalar_one_or_none()

    if persona is None:
        raise ValueError(f"Candidate persona not found for id: {persona_id}")

    target_roles = persona.target_roles or []
    persona_skills_lower = {
        s.skill_name.strip().lower() for s in (persona.skills or [])
    }

    # 2. Query top 50 active jobs matching target roles
    query = (
        select(JobListing)
        .where(JobListing.status == "active")
        .order_by(JobListing.created_at.desc())
    )

    if target_roles:
        role_clauses = [JobListing.title.ilike(f"%{r}%") for r in target_roles]
        query = query.where(or_(*role_clauses))

    query = query.limit(50)
    jobs_res = await db.execute(query)
    jobs = jobs_res.scalars().all()

    if not jobs:
        # Fallback to general active jobs
        fb_query = (
            select(JobListing)
            .where(JobListing.status == "active")
            .order_by(JobListing.created_at.desc())
            .limit(50)
        )
        jobs = (await db.execute(fb_query)).scalars().all()

    # 3. Aggregate all required skills from ATS requirements
    skill_counts: Counter[str] = Counter()
    for j in jobs:
        reqs = j.ats_requirements or {}
        h_skills = reqs.get("hard_skills", [])
        for s in h_skills:
            if s and len(s) > 1:
                skill_counts[s.strip()] += 1

    total_jobs = max(1, len(jobs))
    top_market_skills: list[dict[str, Any]] = []
    top_gaps: list[MarketSkillGapItem] = []

    for skill, count in skill_counts.most_common(12):
        pct = int(round((count / total_jobs) * 100))
        top_market_skills.append(
            {
                "skill": skill,
                "demand_pct": pct,
                "job_count": count,
                "in_persona": skill.lower() in persona_skills_lower,
            }
        )

        if skill.lower() not in persona_skills_lower and pct >= 25:
            top_gaps.append(
                MarketSkillGapItem(
                    skill=skill,
                    market_demand_pct=pct,
                    unlocked_jobs_count=count,
                )
            )

    # 4. Generate actionable upskilling pathways
    upskilling_pathways: list[dict[str, str]] = []
    for gap in top_gaps[:3]:
        upskilling_pathways.append(
            {
                "skill": gap.skill,
                "action": (
                    f"Build a production service or open-source repo for "
                    f"{gap.skill} to unlock up to {gap.unlocked_jobs_count} "
                    f"matching jobs."
                ),
                "impact": f"+{gap.market_demand_pct}% market alignment",
            }
        )

    return PersonaBenchmarkReport(
        persona_id=str(persona.id),
        persona_name=persona.name,
        target_roles=target_roles,
        analyzed_jobs_count=len(jobs),
        top_market_skills=top_market_skills,
        top_skill_gaps=top_gaps[:5],
        upskilling_pathways=upskilling_pathways,
    )
