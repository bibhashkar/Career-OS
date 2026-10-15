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
# Tier 0: Holistic 360° Candidate Audit Schemas
# ---------------------------------------------------------------------------
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
