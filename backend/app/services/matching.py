"""
Two-stage candidate-to-job retrieval, ranking, and probability scoring engine.

This service implements the algorithms documented in ADR-008:
  - Stage 1: Deterministic relational SQL pre-filter (<15ms, bounded to 250 jobs).
  - Stage 2: Multi-factor precision reranker calculating Acceptance
    Probability P(Match).
  - Bayesian uncertainty gate G_prob for unconfirmed visa sponsorship or location.
  - Signal boosters for employer/university pedigree (S_prestige), hackathons
    and open-source leadership (S_achievement), and posting freshness (S_freshness).
"""

from __future__ import annotations

import logging
import math
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.tools.embeddings import generate_deterministic_embedding
from app.ingestion.deterministic_extractor import (
    classify_industry_vertical,
    extract_domain_strictness,
)
from app.models.cv_block import CVBlock
from app.models.job_listing import JobListing
from app.models.user_account import (
    CandidatePersona,
    JobMatchCache,
    PersonaSkill,
    UserAccount,
)
from app.services.skill_graph import (
    compute_asymmetric_skill_score,
    get_transfer_weight,
    normalize_skill,
)

logger = logging.getLogger("career_os.services.matching")

# ---------------------------------------------------------------------------
# Prestige & Institution Tier Taxonomy
# ---------------------------------------------------------------------------
TIER_1_ORGANIZATIONS = {
    # FAANG / Hyperscalers
    "google",
    "alphabet",
    "meta",
    "facebook",
    "apple",
    "amazon",
    "microsoft",
    "netflix",
    # Top Quant / HFT
    "jane street",
    "citadel",
    "hrt",
    "hudson river trading",
    "two sigma",
    "optiver",
    "jump trading",
    "de shaw",
    # Tier-1 Scaleups / AI Labs
    "stripe",
    "openai",
    "databricks",
    "anthropic",
    "snowflake",
    "uber",
    "airbnb",
    "palantir",
    # Top-Ranked Computer Science Institutions
    "mit",
    "massachusetts institute of technology",
    "stanford",
    "stanford university",
    "berkeley",
    "uc berkeley",
    "carnegie mellon",
    "cmu",
    "harvard",
    "caltech",
    "princeton",
    "oxford",
    "cambridge",
    "eth zurich",
    "tsinghua",
    "iit",
}

TIER_2_ORGANIZATIONS = {
    "salesforce",
    "adobe",
    "spotify",
    "shopify",
    "coinbase",
    "twilio",
    "pinterest",
    "lyft",
    "dropbox",
    "gitlab",
    "github",
    "atlassian",
    "nvidia",
    "intel",
    "amd",
    "cisco",
    "oracle",
    "columbia university",
    "cornell",
    "georgia tech",
    "uiuc",
    "university of washington",
    "waterloo",
    "university of michigan",
    "ucla",
    "nyu",
}

# ---------------------------------------------------------------------------
# Semantic Phrasing & Cross-Tech Equivalence Matrix
# ---------------------------------------------------------------------------
TECH_EQUIVALENCES: dict[str, set[str]] = {
    "aws": {"gcp", "azure", "google cloud", "cloud"},
    "gcp": {"aws", "azure", "google cloud platform"},
    "azure": {"aws", "gcp"},
    "kubernetes": {"docker", "ecs", "nomad", "containerization"},
    "docker": {"kubernetes", "containerization", "podman"},
    "kafka": {"rabbitmq", "pulsar", "kinesis", "eventbridge", "nats"},
    "rabbitmq": {"kafka", "pulsar", "activemq"},
    "postgresql": {"mysql", "relational database", "sqlite"},
    "mysql": {"postgresql", "mariadb"},
    "fastapi": {"flask", "django", "express", "gin"},
    "flask": {"fastapi", "django"},
    "django": {"fastapi", "flask"},
    "react": {"vue", "angular", "next.js", "svelte"},
    "vue": {"react", "angular"},
    "dynamodb": {"mongodb", "cassandra", "couchbase"},
    "mongodb": {"dynamodb", "couchbase", "documentdb"},
}

# Seniority weights
SENIORITY_RANKS = {
    "intern": 0,
    "junior": 1,
    "entry": 1,
    "mid": 2,
    "mid-level": 2,
    "senior": 3,
    "lead": 4,
    "staff": 5,
    "principal": 6,
    "director": 7,
}

# ---------------------------------------------------------------------------
# DOL / USCIS H-1B Prevailing Wage Fallback Estimates (Annualized USD Base)
# ---------------------------------------------------------------------------
PREVAILING_WAGE_ESTIMATES: dict[str, int] = {
    "intern": 80_000,
    "entry": 110_000,
    "junior": 120_000,
    "mid": 150_000,
    "mid-level": 150_000,
    "senior": 185_000,
    "lead": 210_000,
    "staff": 235_000,
    "principal": 265_000,
    "director": 280_000,
}


class MatchFactorBreakdown(BaseModel):
    """Detailed score decomposition for matching transparency."""

    g_prob: float = Field(..., description="Bayesian gate multiplier [0.0, 1.0].")
    skill_score: float = Field(..., description="Skill overlap factor [0.0, 1.0].")
    semantic_score: float = Field(..., description="Vector cosine similarity.")
    seniority_score: float = Field(..., description="Experience alignment score.")
    prestige_booster: float = Field(..., description="Company/School prestige factor.")
    achievement_booster: float = Field(..., description="Hackathons/Honors booster.")
    freshness_booster: float = Field(..., description="Posting recency advantage.")
    d_core: float = Field(1.0, description="Core dealbreaker multiplier [0.25, 1.0].")
    archetype_score: float = Field(
        0.0, description="Company trait & candidate proof alignment."
    )
    domain_score: float = Field(
        0.0, description="Domain alignment factor S_domain [0.0, 1.0]."
    )
    context_score: float = Field(
        0.0, description="Blended context alignment factor S_context [0.0, 1.0]."
    )
    comp_score: float = Field(
        1.0, description="Compensation feasibility factor [0.0, 1.0]."
    )


class JobMatchResult(BaseModel):
    """Final scored job listing opportunity returned to candidate feed."""

    job_id: str
    title: str
    company_name: str
    location: str
    workplace_type: str
    salary_range: str | None = None
    visa_sponsorship: str | None = None
    apply_url: str | None = None
    posted_at: datetime | None = None
    match_score: float = Field(..., description="P(Match) acceptance probability.")
    hard_gate_pass: bool
    probability_band: str = Field(..., description="'high', 'moderate', or 'low'")
    breakdown: MatchFactorBreakdown
    matched_skills: list[str] = Field(default_factory=list)
    missing_dealbreakers: list[str] = Field(default_factory=list)
    phrasing_equivalents: list[dict[str, str]] = Field(default_factory=list)
    gate_notes: list[str] = Field(default_factory=list)


def calculate_prestige_score(organizations: list[str]) -> float:
    """
    Score candidate pedigree based on prior employers and academic institutions.

    Returns:
        1.0 for Tier-1 (FAANG, Top Quant, Top CS schools).
        0.8 for Tier-2 (Established public tech, top research universities).
        0.5 for Tier-3 (Mid-market technology enterprises).
        0.3 baseline for unlisted organizations.
    """
    if not organizations:
        return 0.3

    score = 0.3
    for org in organizations:
        clean = org.strip().lower()
        if any(t1 in clean for t1 in TIER_1_ORGANIZATIONS):
            return 1.0
        if any(t2 in clean for t2 in TIER_2_ORGANIZATIONS):
            score = max(score, 0.8)
        elif len(clean) > 3:
            score = max(score, 0.5)

    return score


def calculate_achievement_score(blocks: list[CVBlock]) -> float:
    """
    Extract achievement merit markers (hackathons, open-source, publications).

    Returns:
        1.0 for 1st/2nd/3rd place finishes in recognized hackathons or major OSS.
        0.85 for peer-reviewed papers (NeurIPS/ICML/IEEE) or patented tech.
        0.60 for general hackathon participation or quantified distinction.
        0.20 baseline standard experience.
    """
    score = 0.2
    for b in blocks:
        cat = (b.category or "").lower()
        title_lower = (b.title or "").lower()
        content_lower = (b.content or "").lower()
        metrics = b.metrics or {}

        # 1. Hackathon awards
        if "hackathon" in cat or "hackathon" in title_lower:
            placement = str(metrics.get("placement", "")).lower()
            if any(w in placement for w in ["1st", "winner", "first", "2nd", "3rd"]):
                return 1.0
            if any(
                w in content_lower
                for w in ["1st place", "winner", "top 3", "grand prize"]
            ):
                return 1.0
            score = max(score, 0.6)

        # 2. Open-source leadership & GitHub stars
        if "open_source" in cat or "github" in content_lower:
            stars = metrics.get("github_stars", 0)
            if isinstance(stars, (int, float)) and stars >= 500:
                return 1.0
            score = max(score, 0.75)

        # 3. Peer-reviewed research & patents
        if "publication" in cat or any(
            p in content_lower for p in ["neurips", "icml", "ieee", "acm", "patent"]
        ):
            score = max(score, 0.85)

    return score


def calculate_freshness_score(
    posted_at: datetime | None,
    created_at: datetime | None,
) -> float:
    """
    Calculate application timing advantage based on listing activation recency.

    Applications within 72 hours receive a 3.8x recruiter callback multiplier:
      - 0 to 3 days: 1.0
      - 4 to 14 days: 0.75
      - 15 to 30 days: 0.45
      - > 30 days: 0.15
    """
    ref_time = posted_at or created_at
    if ref_time is None:
        return 0.60

    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=UTC)

    age_days = (datetime.now(UTC) - ref_time).total_seconds() / 86400.0

    if age_days <= 3.0:
        return 1.0
    if age_days <= 14.0:
        return 0.75
    if age_days <= 30.0:
        return 0.45
    return 0.15


# ---------------------------------------------------------------------------
# Compensation Normalization & Feasibility Engine
# ---------------------------------------------------------------------------
def normalize_job_compensation(job: JobListing) -> tuple[int, int, bool]:
    """
    Extract annualized USD base salary bounds (min_salary, max_salary, is_estimated).

    If job has explicit salary_min / salary_max, uses them.
    Otherwise parses salary_range regex.
    If unstated or unparseable, falls back to DOL/USCIS H-1B prevailing wage
    estimates calibrated by role seniority and industry sector.
    """
    if job.salary_max is not None and job.salary_max > 0:
        c_min = job.salary_min or int(job.salary_max * 0.8)
        return c_min, job.salary_max, bool(job.is_salary_estimated)

    raw = (job.salary_range or "").strip()
    if raw:
        # Match "$180,000 - $220,000", "$190k - $240k", "$140K-$160K"
        pattern = re.compile(
            r"\$?(\d{1,3}(?:,\d{3})+|\d+)\s*([kK])?\s*(?:-|–|—|to)\s*\$?(\d{1,3}(?:,\d{3})+|\d+)\s*([kK])?"
        )
        match = pattern.search(raw)
        if match:
            g1, k1, g2, k2 = match.groups()
            v1 = int(g1.replace(",", ""))
            v2 = int(g2.replace(",", ""))
            if k1 or (k2 and v1 < 1000):
                v1 *= 1000
            if k2 or (k1 and v2 < 1000):
                v2 *= 1000
            if v1 > 0 and v2 >= v1:
                return v1, v2, False

    reqs = job.ats_requirements or {}
    seniority = (reqs.get("seniority_level") or "mid").strip().lower()
    base_est = PREVAILING_WAGE_ESTIMATES.get(seniority, 150_000)
    industry = (job.industry or "").strip().lower()
    if industry in {"hft_quant_trading", "ai_ml_infra"}:
        base_est = int(base_est * 1.25)
    c_min = int(base_est * 0.85)
    c_max = int(base_est * 1.15)
    return c_min, c_max, True


def calculate_compensation_score(
    persona_min_salary: int | None,
    job: JobListing,
) -> float:
    """
    Calculate compensation feasibility S_comp with exponential shortfall penalty.

    If candidate min_salary is unspecified (None or <= 0), returns 1.0.
    If job max salary meets or exceeds candidate requirement, returns 1.0.
    If job max salary is below candidate requirement:
        S_comp = exp(-3.0 * (C_target - C_max) / C_target)
    """
    if persona_min_salary is None or persona_min_salary <= 0:
        return 1.0

    _, c_max, _ = normalize_job_compensation(job)
    if c_max >= persona_min_salary:
        return 1.0

    shortfall_ratio = (persona_min_salary - c_max) / float(persona_min_salary)
    score = math.exp(-3.0 * shortfall_ratio)
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------------------------
# Job Archetype Alignment Engine
# ---------------------------------------------------------------------------
def calculate_archetype_score(
    job: JobListing,
    prestige_score: float,
    achievement_score: float,
    blocks: list[CVBlock],
) -> float:
    """
    Calculate job-specific archetype alignment S_archetype.

    Eliminates Job-Invariant Factor Collapse by projecting a 4D candidate proof
    vector onto the job/company's trait vector:
      Candidate Proof P_cand = [S_prestige, S_achievement, S_scale, S_oss]
      Job Trait A_job        = [w_pedigree, w_innovation, w_scale, w_oss]
      S_archetype            = (A_job . P_cand) / sum(A_job)
    """
    # 1. Candidate Proof Vector P_cand
    p_scale = 0.20
    p_oss = 0.20
    for b in blocks:
        metrics = b.metrics or {}
        content_lower = (b.content or "").lower()
        cat_lower = (b.category or "").lower()

        # Throughput / Latency / Scale proof
        if "throughput_or_latency" in metrics or any(
            w in content_lower
            for w in [
                "req/s",
                "qps",
                "rps",
                "p99",
                "million",
                "billion",
                "petabyte",
                "terabyte",
                "distributed",
            ]
        ):
            p_scale = max(
                p_scale,
                0.85 if ("p99" in content_lower or "req/s" in content_lower) else 0.60,
            )

        # Open-source distinction
        if "open_source" in cat_lower or "github" in content_lower:
            stars = metrics.get("github_stars", 0)
            if isinstance(stars, (int, float)) and stars >= 500:
                p_oss = 1.0
            else:
                p_oss = max(p_oss, 0.70)

    p_cand = [
        max(0.0, min(1.0, prestige_score)),
        max(0.0, min(1.0, achievement_score)),
        max(0.0, min(1.0, p_scale)),
        max(0.0, min(1.0, p_oss)),
    ]

    # 2. Company / Job Trait Vector A_job = [w_pedigree, w_innovation, w_scale, w_oss]
    industry = (job.industry or "").lower()
    company_lower = (job.company_name or "").lower()
    desc_lower = (job.raw_description or "").lower()
    title_lower = (job.title or "").lower()

    if (
        "quant" in industry
        or "hft" in industry
        or any(
            q in company_lower
            for q in ["jane street", "citadel", "hrt", "two sigma", "jump trading"]
        )
    ):
        a_job = [1.0, 0.40, 0.90, 0.20]
    elif (
        "ai_ml" in industry
        or "ai" in industry
        or any(ai in company_lower for ai in ["openai", "anthropic", "deepmind"])
        or "ai platform" in title_lower
        or "machine learning" in title_lower
    ):
        a_job = [0.70, 1.0, 0.80, 0.60]
    elif (
        "devtools" in industry
        or "developer_tools" in industry
        or "open source" in desc_lower
        or any(d in company_lower for d in ["github", "gitlab", "docker", "postman"])
    ):
        a_job = [0.30, 0.70, 0.50, 1.0]
    elif (job.ats_board and getattr(job.ats_board, "tier", 2) == 1) or any(
        t1 in company_lower for t1 in TIER_1_ORGANIZATIONS
    ):
        a_job = [0.90, 0.70, 0.80, 0.40]
    else:
        a_job = [0.50, 0.50, 0.60, 0.40]

    # Modulate with job description keywords
    if any(
        w in desc_lower
        for w in [
            "low latency",
            "microsecond",
            "throughput",
            "scale",
            "distributed systems",
        ]
    ):
        a_job[2] = min(1.0, a_job[2] + 0.20)
    if any(
        w in desc_lower
        for w in ["open source", "public repo", "community", "contributions", "sdk"]
    ):
        a_job[3] = min(1.0, a_job[3] + 0.20)
    if any(
        w in desc_lower
        for w in ["research", "publication", "patent", "phd", "state-of-the-art"]
    ):
        a_job[1] = min(1.0, a_job[1] + 0.20)

    dot = sum(a * p for a, p in zip(a_job, p_cand, strict=False))
    norm = sum(a_job)
    return max(0.0, min(1.0, dot / max(0.001, norm)))


# ---------------------------------------------------------------------------
# Explicit Domain Alignment Engine (S_domain & S_context)
# ---------------------------------------------------------------------------
def derive_candidate_domain_profile(
    persona: CandidatePersona,
    blocks: list[CVBlock],
) -> tuple[dict[str, float], dict[str, float]]:
    """
    Derive candidate's normalized domain distribution vector D_cand and tenure.

    For each block b in blocks:
      - Determines block vertical tags from b.industry_tags or classifies via
        classify_industry_vertical(b.title, b.content, b.organization).
      - Determines duration Duration(b) (from b.metrics['duration_years'], defaulting to
        persona.years_experience / max(1, len(blocks))).
      - Applies age decay gamma = 0.90 based on block chronological order.

    Returns:
      (domain_distribution: dict[str, float], yoe_domain: dict[str, float])
    """
    if not blocks:
        # Fallback to persona headline, target roles, and summary
        persona_text = (
            f"{persona.headline or ''} {' '.join(persona.target_roles or [])}"
        )
        detected = classify_industry_vertical(persona.headline or "", persona_text)
        if detected != "general_saas":
            yoe = float(persona.years_experience or 0)
            return {detected: 1.0}, {detected: yoe}
        return {}, {}

    gamma = 0.90
    decayed_weights: dict[str, float] = {}
    total_yoe: dict[str, float] = {}
    default_duration = max(
        0.5, float(persona.years_experience or 1.0) / max(1, len(blocks))
    )

    for idx, b in enumerate(blocks):
        # 1. Resolve vertical tags
        tags: list[str] = list(getattr(b, "industry_tags", []) or [])
        if not tags:
            detected = classify_industry_vertical(
                b.title or "", b.content or "", b.organization or ""
            )
            tags = [detected]

        # 2. Resolve block duration
        metrics = b.metrics or {}
        duration = float(
            metrics.get("duration_years") or metrics.get("years") or default_duration
        )

        # 3. Recency decay weight: Age index idx (0 is newest, 1 is older, etc.)
        age_weight = duration * (gamma**idx)

        # Distribute weight evenly across block's industry tags
        tag_share = 1.0 / max(1, len(tags))
        for tag in tags:
            tag_norm = tag.lower().strip()
            decayed_weights[tag_norm] = decayed_weights.get(tag_norm, 0.0) + (
                age_weight * tag_share
            )
            total_yoe[tag_norm] = total_yoe.get(tag_norm, 0.0) + (duration * tag_share)

    # Normalize decayed distribution vector D_cand
    total_decayed = sum(decayed_weights.values())
    domain_dist: dict[str, float] = {}
    if total_decayed > 0:
        for k, v in decayed_weights.items():
            domain_dist[k] = v / total_decayed

    return domain_dist, total_yoe


def calculate_domain_score(
    persona: CandidatePersona,
    blocks: list[CVBlock],
    job: JobListing,
    candidate_domain_profile: tuple[dict[str, float], dict[str, float]] | None = None,
) -> tuple[float, float]:
    """
    Compute candidate's Domain Match Score S_domain and strictness beta_domain.

    S_domain = (D_cand . D_job) * TenureBonus(YoE_domain)
    TenureBonus(YoE) = min(1.0, 0.50 + 0.10 * min(YoE, 5) + 0.02 * max(0, YoE - 5))

    Returns:
        (s_domain: float, beta_domain: float)
    """
    # 1. Resolve job industry vertical and strictness
    vertical = (job.industry_vertical or "").strip().lower()
    strictness = getattr(job, "domain_strictness", None)

    if not vertical or vertical == "general_saas":
        detected_v = classify_industry_vertical(
            job.title or "", job.raw_description or "", job.company_name or ""
        )
        if detected_v != "general_saas":
            vertical = detected_v
        else:
            vertical = "general_saas"

    if strictness is None:
        strictness = extract_domain_strictness(
            job.title or "", job.raw_description or "", vertical
        )
    beta = float(strictness)

    # If role is domain-agnostic SaaS or strictness is 0, domain score is neutral
    if vertical == "general_saas" or beta <= 0.0:
        return 0.50, 0.0

    # 2. Get candidate domain distribution and tenure
    if candidate_domain_profile is not None:
        domain_dist, total_yoe = candidate_domain_profile
    else:
        domain_dist, total_yoe = derive_candidate_domain_profile(persona, blocks)

    d_cand = domain_dist.get(vertical, 0.0)
    yoe = total_yoe.get(vertical, 0.0)

    # 3. TenureBonus curve
    if yoe <= 0.0 or d_cand <= 0.0:
        return 0.0, beta

    tenure_bonus = min(1.0, 0.50 + 0.10 * min(yoe, 5.0) + 0.02 * max(0.0, yoe - 5.0))
    s_domain = max(0.0, min(1.0, d_cand * tenure_bonus))

    return s_domain, beta


def calculate_match_upgraded(
    persona: CandidatePersona,
    job: JobListing,
    blocks: list[CVBlock] | None = None,
    persona_skills: set[str] | None = None,
    account: UserAccount | None = None,
) -> tuple[float, MatchFactorBreakdown]:
    """
    Pure evaluation function computing P(Match) with full factor breakdown:
    P(Match) = (G_prob * D_core) * [
        0.25 * S_skills + 0.25 * S_semantic + 0.15 * S_seniority
        + 0.15 * S_context + 0.10 * S_comp + 0.10 * S_freshness
    ]
    where S_context = (1 - beta_domain) * S_archetype + beta_domain * S_domain.
    """
    active_blocks = blocks or []
    target_roles = [r.lower() for r in (persona.target_roles or [])]

    # Resolve candidate skills
    cand_skills: set[str] = set(persona_skills or set())
    for b in active_blocks:
        for s in b.skills or []:
            cand_skills.add(s)

    reqs = job.ats_requirements or {}
    job_skills = reqs.get("hard_skills", [])
    if not job_skills:
        job_skills = [
            s for s in cand_skills if s.lower() in (job.raw_description or "").lower()
        ]

    # 1. Asymmetric skills
    core_skills = reqs.get("core_skills") or reqs.get("dealbreakers")
    eval_res = compute_asymmetric_skill_score(
        candidate_skills=cand_skills,
        job_skills=job_skills,
        core_job_skills=core_skills,
        cv_block_count=len(active_blocks),
    )
    s_skills = eval_res.skill_score
    d_core = eval_res.d_core

    # 2. Semantic
    s_semantic = calculate_semantic_top3_score(
        blocks=active_blocks,
        job=job,
        target_roles=target_roles,
    )

    # 3. Seniority
    job_exp_years = reqs.get("years_experience_min")
    job_sen = reqs.get("seniority_level")
    s_seniority = calculate_seniority_score(
        candidate_years=persona.years_experience,
        candidate_seniority=persona.seniority_level,
        job_seniority=job_sen,
        job_min_years=job_exp_years,
    )

    # 4. Archetype & Domain alignment
    organizations = [b.organization for b in active_blocks if b.organization]
    prestige_score = calculate_prestige_score(organizations)
    achievement_score = calculate_achievement_score(active_blocks)
    s_archetype = calculate_archetype_score(
        job=job,
        prestige_score=prestige_score,
        achievement_score=achievement_score,
        blocks=active_blocks,
    )
    s_domain, beta_domain = calculate_domain_score(
        persona=persona,
        blocks=active_blocks,
        job=job,
    )
    s_context = (1.0 - beta_domain) * s_archetype + beta_domain * s_domain

    # 5. Compensation
    s_comp = calculate_compensation_score(
        persona_min_salary=persona.min_salary,
        job=job,
    )

    # 6. Freshness
    s_freshness = calculate_freshness_score(job.posted_at, job.created_at)

    # 7. Gate
    if account is not None:
        g_prob, _, _ = calculate_probabilistic_gate(
            candidate_visa=account.visa_status,
            job_visa=job.visa_sponsorship,
            candidate_locations=account.preferred_locations,
            candidate_remote=account.remote_preference,
            job_location=job.raw_location,
            job_workplace=job.workplace_type,
            job_country_code=job.country_code,
        )
    else:
        g_prob = 1.0

    # 8. Master Equation
    weighted_core = (
        (0.25 * s_skills)
        + (0.25 * s_semantic)
        + (0.15 * s_seniority)
        + (0.15 * s_context)
        + (0.10 * s_comp)
        + (0.10 * s_freshness)
    )
    p_match = round((g_prob * d_core) * weighted_core, 4)

    breakdown = MatchFactorBreakdown(
        g_prob=round(g_prob, 2),
        skill_score=round(s_skills, 2),
        semantic_score=round(s_semantic, 2),
        seniority_score=round(s_seniority, 2),
        prestige_booster=round(prestige_score, 2),
        achievement_booster=round(achievement_score, 2),
        freshness_booster=round(s_freshness, 2),
        d_core=round(d_core, 2),
        archetype_score=round(s_archetype, 2),
        domain_score=round(s_domain, 2),
        context_score=round(s_context, 2),
        comp_score=round(s_comp, 2),
    )
    return p_match, breakdown


# ---------------------------------------------------------------------------
# Vector Semantic Alignment Engine (Top-3 Block Max-Sim)
# ---------------------------------------------------------------------------
def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2, strict=False):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0
    return dot / (math.sqrt(norm1) * math.sqrt(norm2))


def _resolve_vector(raw: Any | None, fallback_text: str) -> list[float]:
    """Extract list[float] from vector column or generate deterministic embedding."""
    if raw is not None:
        if isinstance(raw, list):
            return [float(x) for x in raw]
        if hasattr(raw, "tolist"):
            return [float(x) for x in raw.tolist()]
        try:
            return [float(x) for x in raw]
        except (TypeError, ValueError):
            pass
    return generate_deterministic_embedding(fallback_text)


def calculate_semantic_top3_score(
    blocks: list[CVBlock],
    job: JobListing,
    target_roles: list[str],
) -> float:
    """
    Calculate Top-3 Block Max-Sim semantic score S_semantic.

    Eliminates the double-counting bug by evaluating true vector cosine similarity
    between unit-normalized CVBlock embeddings and the job embedding.
    """
    job_text = f"{job.title} {job.raw_description or ''}"
    job_vec = _resolve_vector(job.embedding, job_text)

    # 1. Block similarities
    block_sims: list[float] = []
    for b in blocks:
        block_text = f"{b.title} {b.content or ''}"
        b_vec = _resolve_vector(b.embedding, block_text)
        sim = _cosine_similarity(b_vec, job_vec)
        weight = getattr(b, "priority_weight", 1.0) or 1.0
        weighted_sim = max(0.0, min(1.0, sim * weight))
        block_sims.append(weighted_sim)

    if block_sims:
        block_sims.sort(reverse=True)
        top3 = block_sims[:3]
        weights = [0.50, 0.30, 0.20][: len(top3)]
        total_w = sum(weights)
        top3_sim = sum(s * w for s, w in zip(top3, weights, strict=False)) / total_w
    else:
        top3_sim = 0.50

    # 2. Role Title semantic alignment
    role_match = 0.50
    title_lower = (job.title or "").lower()
    if target_roles:
        if any(r.lower() in title_lower for r in target_roles):
            role_match = 1.0
        else:
            tokens = [w for r in target_roles for w in r.lower().split() if len(w) > 2]
            overlap = sum(1 for tok in tokens if tok in title_lower)
            role_match = min(0.90, 0.40 + 0.15 * overlap)

    s_semantic = (0.70 * top3_sim) + (0.30 * role_match)
    return max(0.0, min(1.0, s_semantic))


def calculate_skill_overlap(
    candidate_skills: set[str],
    job_skills: list[str],
    candidate_skills_lower: set[str] | None = None,
) -> tuple[float, list[str], list[str], list[dict[str, str]]]:
    """
    Calculate normalized skill overlap and discover cross-technology matches.

    Args:
        candidate_skills: Set of raw candidate skills.
        job_skills: List of required job skills.
        candidate_skills_lower: Optional pre-computed lowercased candidate skill set
            to eliminate redundant set allocations in tight evaluation loops.

    Returns:
        (overlap_ratio, matched_skills, missing_skills, phrasing_equivalents)
    """
    cand_lower = (
        candidate_skills_lower
        if candidate_skills_lower is not None
        else {normalize_skill(s) for s in candidate_skills if normalize_skill(s)}
    )
    clean_job_skills = [normalize_skill(s) for s in job_skills if normalize_skill(s)]

    if not clean_job_skills:
        # Neutral score if job does not declare explicit skill requirements
        return 0.70, list(candidate_skills)[:5], [], []

    matched: list[str] = []
    missing: list[str] = []
    equivalents: list[dict[str, str]] = []

    for js in clean_job_skills:
        if js in cand_lower:
            matched.append(js)
            continue

        # Check skill graph asymmetric transfer
        best_u: str | None = None
        best_transfer = 0.0
        for cand_s in cand_lower:
            tw = get_transfer_weight(cand_s, js)
            if tw > best_transfer:
                best_transfer = tw
                best_u = cand_s

        # Also check symmetric equivalence map
        eq_set = TECH_EQUIVALENCES.get(js, set())
        overlap_eq = eq_set.intersection(cand_lower)

        if best_transfer >= 0.30 and best_u:
            matched.append(js)
            equivalents.append(
                {
                    "job_term": js.title(),
                    "candidate_has": best_u.title(),
                }
            )
        elif overlap_eq:
            matched.append(js)
            cand_alt = next(iter(overlap_eq))
            equivalents.append(
                {
                    "job_term": js.title(),
                    "candidate_has": cand_alt.title(),
                }
            )
        else:
            missing.append(js)

    overlap_ratio = len(matched) / max(1, len(clean_job_skills))
    return min(1.0, overlap_ratio), matched, missing, equivalents


def calculate_seniority_score(
    candidate_years: int,
    candidate_seniority: str,
    job_seniority: str | None,
    job_min_years: int | None,
) -> float:
    """
    Calibrate seniority level alignment between candidate and role.
    """
    cand_rank = SENIORITY_RANKS.get(candidate_seniority.lower(), 2)
    job_rank = SENIORITY_RANKS.get((job_seniority or "").lower(), cand_rank)

    # Difference in hierarchy levels
    diff = cand_rank - job_rank
    if diff == 0:
        base_score = 1.0
    elif diff == 1:
        base_score = 0.90  # Slightly senior for role
    elif diff == -1:
        base_score = 0.75  # Slightly junior
    elif diff > 1:
        base_score = 0.70  # Overqualified
    else:
        base_score = 0.40  # Significantly under-tenured

    # Factor in explicit years of experience if declared
    if job_min_years is not None and job_min_years > 0:
        if candidate_years >= job_min_years:
            base_score = min(1.0, base_score + 0.1)
        else:
            shortfall = job_min_years - candidate_years
            base_score = max(0.2, base_score - (0.15 * shortfall))

    return max(0.0, min(1.0, base_score))


def calculate_probabilistic_gate(
    candidate_visa: str,
    job_visa: str | None,
    candidate_locations: list[str],
    candidate_remote: str,
    job_location: str,
    job_workplace: str,
    job_country_code: str | None,
) -> tuple[float, bool, list[str]]:
    """
    Compute Bayesian uncertainty gate G_prob and hard-pass eligibility.

    Rules:
      - Visa:
        - Candidate requires visa:
          - job_visa == 'no': G_prob = 0.0 (Hard gate failure).
          - job_visa == 'yes': G_prob = 1.0.
          - job_visa is None: G_prob = 0.85 (Bayesian uncertainty discount).
        - Candidate domestic/citizen: G_prob = 1.0.
      - Workplace/Location:
        - Conflicting on-site location outside candidate region: G_prob = 0.0.
        - Permissive remote/hybrid match: G_prob = 1.0 (or 0.90 for unconfirmed scope).
    """
    g_prob = 1.0
    hard_pass = True
    notes: list[str] = []

    # 1. Visa Sponsorship Evaluation
    requires_visa = candidate_visa.strip().lower() in {
        "h-1b",
        "f-1 opt",
        "requires_sponsorship",
        "requires sponsorship",
        "work_permit",
    }

    if requires_visa:
        job_v = (job_visa or "").strip().lower()
        if job_v == "no":
            g_prob = 0.0
            hard_pass = False
            notes.append("Employer explicitly does not sponsor visas.")
        elif job_v in {"yes", "transfer_only", "opt_cpt_accepted"}:
            notes.append("Verified visa sponsorship supported.")
        else:
            # Missing parameter: apply Bayesian uncertainty discount
            g_prob *= 0.85
            notes.append(
                "Visa sponsorship policy unconfirmed; uncertainty discount applied."
            )
    else:
        notes.append("Domestic work authorization; visa gate passed.")

    # 2. Location & Modality Evaluation
    job_loc_lower = (job_location or "").lower()
    workplace_lower = (job_workplace or "").lower()
    cand_pref_lower = candidate_remote.strip().lower()

    if cand_pref_lower == "remote":
        if workplace_lower == "remote" or "remote" in job_loc_lower:
            notes.append("Remote modality aligned.")
        elif workplace_lower == "on_site":
            # Check if candidate listed this city explicitly
            matched_loc = any(
                loc.lower() in job_loc_lower
                for loc in candidate_locations
                if loc.lower() != "remote"
            )
            if not matched_loc:
                g_prob = 0.0
                hard_pass = False
                notes.append("On-site requirement outside target commuting zone.")
        else:
            g_prob *= 0.90
            notes.append("Hybrid or flexible workplace arrangement.")

    return g_prob, hard_pass, notes


async def retrieve_stage1_candidates(
    db: AsyncSession,
    persona: CandidatePersona,
    account: UserAccount,
    blocks: list[CVBlock],
    persona_skills: set[str],
    candidate_skills_lower: set[str],
    candidate_vector: list[float] | None = None,
    modality_filter: str | None = None,
    visa_filter: bool | None = None,
    search_query: str | None = None,
    location_filter: str | None = None,
    posted_within_days: int | None = None,
    limit: int = 250,
) -> list[JobListing]:
    """
    Stage 1 Hybrid Inverted Index & Reciprocal Rank Fusion (RRF) Retrieval.

    Defeats recency starvation by combining three ranking streams:
      - Stream 1: Skill & Role Alignment
      - Stream 2: Vector Cosine Similarity
      - Stream 3: Posting Recency
    Fused using RRF (k = 60) to select top candidate listings for Stage 2.
    """
    requires_visa = account.visa_status.strip().lower() in {
        "h-1b",
        "f-1 opt",
        "requires_sponsorship",
        "requires sponsorship",
    }
    target_roles = [r.lower() for r in (persona.target_roles or [])]

    base_query = (
        select(JobListing)
        .options(selectinload(JobListing.ats_board))
        .where(JobListing.status == "active")
    )

    # Hard negative visa exclusion
    if requires_visa or visa_filter:
        base_query = base_query.where(
            or_(
                JobListing.visa_sponsorship.is_(None),
                JobListing.visa_sponsorship != "no",
            )
        )

    # Modality filter
    if modality_filter:
        base_query = base_query.where(
            JobListing.workplace_type == modality_filter.lower()
        )

    # Location filter (city, state, country, region, raw location)
    if location_filter and location_filter.strip():
        loc_term = f"%{location_filter.strip()}%"
        loc_code = location_filter.strip()
        base_query = base_query.where(
            or_(
                JobListing.city.ilike(loc_term),
                JobListing.state_province.ilike(loc_term),
                JobListing.state_province_code.ilike(loc_code),
                JobListing.country.ilike(loc_term),
                JobListing.country_code.ilike(loc_code),
                JobListing.primary_region.ilike(loc_term),
                JobListing.raw_location.ilike(loc_term),
            )
        )

    # Search keyword filter (title, company, description)
    if search_query and search_query.strip():
        q_term = f"%{search_query.strip()}%"
        base_query = base_query.where(
            or_(
                JobListing.title.ilike(q_term),
                JobListing.company_name.ilike(q_term),
                JobListing.raw_description.ilike(q_term),
            )
        )

    # Date recency filter
    if posted_within_days and posted_within_days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=posted_within_days)
        base_query = base_query.where(
            or_(
                JobListing.posted_at >= cutoff,
                and_(
                    JobListing.posted_at.is_(None),
                    JobListing.first_seen_at >= cutoff,
                ),
            )
        )

    # Retrieve candidates across multi-streams to prevent recency starvation
    candidate_map: dict[uuid.UUID, JobListing] = {}

    # Stream A: Recency
    recency_stmt = base_query.order_by(
        JobListing.posted_at.desc().nullslast(),
        JobListing.created_at.desc(),
    ).limit(limit)
    recency_res = await db.execute(recency_stmt)
    for job in recency_res.scalars().all():
        candidate_map[job.id] = job

    # Stream B: Role Title Matching (if target_roles specified)
    if target_roles:
        role_clauses = [JobListing.title.ilike(f"%{role}%") for role in target_roles]
        role_stmt = base_query.where(or_(*role_clauses)).limit(limit)
        role_res = await db.execute(role_stmt)
        for job in role_res.scalars().all():
            candidate_map[job.id] = job

    # Stream C: Keyword / Core Skill Matching
    if candidate_skills_lower:
        top_skills = sorted(candidate_skills_lower)[:5]
        skill_clauses = [JobListing.raw_description.ilike(f"%{s}%") for s in top_skills]
        skill_stmt = base_query.where(or_(*skill_clauses)).limit(limit)
        skill_res = await db.execute(skill_stmt)
        for job in skill_res.scalars().all():
            candidate_map[job.id] = job

    # Fallback if specific streams were too narrow
    if len(candidate_map) < limit:
        broad_stmt = base_query.limit(limit)
        broad_res = await db.execute(broad_stmt)
        for job in broad_res.scalars().all():
            candidate_map[job.id] = job

    candidate_jobs = list(candidate_map.values())
    if not candidate_jobs:
        return []

    # If total candidate pool is within limit, return candidates directly
    if len(candidate_jobs) <= limit:
        return candidate_jobs

    # Reciprocal Rank Fusion (k = 60)
    # Stream 1: Skill & Role Alignment
    def _stream1_score(job: JobListing) -> float:
        title_lower = (job.title or "").lower()
        role_hit = 1.0 if any(r in title_lower for r in target_roles) else 0.0
        reqs = job.ats_requirements or {}
        job_hard = reqs.get("hard_skills", [])
        if job_hard:
            overlap = sum(
                1 for s in job_hard if normalize_skill(s) in candidate_skills_lower
            )
            skill_hit = overlap / max(1, len(job_hard))
        else:
            skill_hit = 0.5
        return (0.5 * role_hit) + (0.5 * skill_hit)

    # Stream 2: Vector Semantic Alignment
    cand_vec = candidate_vector
    if cand_vec is None:
        cand_summary = (
            f"{persona.headline or ''} {' '.join(target_roles)} "
            f"{' '.join(candidate_skills_lower)}"
        )
        cand_vec = generate_deterministic_embedding(cand_summary)

    def _stream2_score(job: JobListing) -> float:
        job_text = f"{job.title} {job.raw_description or ''}"
        j_vec = _resolve_vector(job.embedding, job_text)
        return _cosine_similarity(cand_vec, j_vec)

    # Stream 3: Recency
    min_dt = datetime.min.replace(tzinfo=UTC)

    def _stream3_key(job: JobListing) -> datetime:
        dt = job.posted_at or job.first_seen_at or job.created_at
        if dt is None:
            return min_dt
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    ranked_stream1 = sorted(candidate_jobs, key=_stream1_score, reverse=True)
    ranked_stream2 = sorted(candidate_jobs, key=_stream2_score, reverse=True)
    ranked_stream3 = sorted(candidate_jobs, key=_stream3_key, reverse=True)

    rank1_map = {job.id: rank for rank, job in enumerate(ranked_stream1, start=1)}
    rank2_map = {job.id: rank for rank, job in enumerate(ranked_stream2, start=1)}
    rank3_map = {job.id: rank for rank, job in enumerate(ranked_stream3, start=1)}

    k = 60.0
    rrf_scores: dict[uuid.UUID, float] = {}
    for job in candidate_jobs:
        r1 = rank1_map[job.id]
        r2 = rank2_map[job.id]
        r3 = rank3_map[job.id]
        rrf = (1.0 / (k + r1)) + (1.0 / (k + r2)) + (1.0 / (k + r3))
        rrf_scores[job.id] = rrf

    candidate_jobs.sort(key=lambda j: rrf_scores[j.id], reverse=True)
    return candidate_jobs[:limit]


async def retrieve_and_rank_jobs(
    db: AsyncSession,
    persona: CandidatePersona,
    account: UserAccount,
    blocks: list[CVBlock],
    page: int = 1,
    page_size: int = 20,
    modality_filter: str | None = None,
    visa_filter: bool | None = None,
    min_score: float = 0.0,
    search_query: str | None = None,
    location_filter: str | None = None,
    posted_within_days: int | None = None,
    sort_by: str = "score",
) -> tuple[list[JobMatchResult], int]:
    """
    Execute two-stage job retrieval, reranking, and persistent caching.

    Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF) Retrieval.
    Stage 2: Precision Multi-Factor Reranker calculating P(Match).
    """
    # Candidate attributes
    target_roles = [r.lower() for r in (persona.target_roles or [])]
    skills_stmt = select(PersonaSkill).where(PersonaSkill.persona_id == persona.id)
    skills_res = await db.execute(skills_stmt)
    persona_skills = {s.skill_name for s in skills_res.scalars().all()}

    # Also aggregate skills from candidate CV blocks for comprehensive coverage
    for b in blocks:
        for s in b.skills or []:
            persona_skills.add(s)

    candidate_skills_lower = {
        normalize_skill(s) for s in persona_skills if normalize_skill(s)
    }

    # -----------------------------------------------------------------------
    # STAGE 1: Hybrid Pre-Filter & Reciprocal Rank Fusion (RRF) Retrieval
    # -----------------------------------------------------------------------
    candidate_jobs = await retrieve_stage1_candidates(
        db=db,
        persona=persona,
        account=account,
        blocks=blocks,
        persona_skills=persona_skills,
        candidate_skills_lower=candidate_skills_lower,
        candidate_vector=None,
        modality_filter=modality_filter,
        visa_filter=visa_filter,
        search_query=search_query,
        location_filter=location_filter,
        posted_within_days=posted_within_days,
        limit=250,
    )

    # -----------------------------------------------------------------------
    # STAGE 2: Precision Multi-Factor Reranker
    # -----------------------------------------------------------------------
    scored_results: list[JobMatchResult] = []

    # Pre-calculate candidate-level constants
    organizations = [b.organization for b in blocks if b.organization]
    prestige_score = calculate_prestige_score(organizations)
    achievement_score = calculate_achievement_score(blocks)
    candidate_domain_profile = derive_candidate_domain_profile(persona, blocks)

    for job in candidate_jobs:
        reqs = job.ats_requirements or {}
        job_skills = reqs.get("hard_skills", [])
        if not job_skills:
            # Fallback to keywords in job description
            job_skills = [
                s
                for s in persona_skills
                if s.lower() in (job.raw_description or "").lower()
            ]

        # 1. Asymmetric Skill Overlap & Core Dealbreaker Multiplier (0.25 weight)
        core_skills = reqs.get("core_skills") or reqs.get("dealbreakers")
        eval_res = compute_asymmetric_skill_score(
            candidate_skills=persona_skills,
            job_skills=job_skills,
            core_job_skills=core_skills,
            cv_block_count=len(blocks),
        )
        s_skills = eval_res.skill_score
        d_core = eval_res.d_core
        matched_s = eval_res.matched_skills
        missing_s = eval_res.missing_skills
        equivs = [
            {
                "job_term": t.job_skill.title(),
                "candidate_has": t.candidate_skill.title(),
            }
            for t in eval_res.transferred_skills
        ]
        # Discover additional phrasing equivalents if available
        for js in missing_s:
            eq_set = TECH_EQUIVALENCES.get(js, set())
            overlap_eq = eq_set.intersection(candidate_skills_lower)
            if overlap_eq:
                cand_alt = next(iter(overlap_eq))
                equivs.append(
                    {
                        "job_term": js.title(),
                        "candidate_has": cand_alt.title(),
                    }
                )

        # 2. Top-3 Block Max-Sim Semantic Similarity (0.25 weight)
        s_semantic = calculate_semantic_top3_score(
            blocks=blocks,
            job=job,
            target_roles=target_roles,
        )

        # 3. Seniority Hierarchy Calibration (0.15 weight)
        job_exp_years = reqs.get("years_experience_min")
        job_sen = reqs.get("seniority_level")
        s_seniority = calculate_seniority_score(
            candidate_years=persona.years_experience,
            candidate_seniority=persona.seniority_level,
            job_seniority=job_sen,
            job_min_years=job_exp_years,
        )

        # 4. Job-Specific Archetype Alignment (0.15 weight)
        s_archetype = calculate_archetype_score(
            job=job,
            prestige_score=prestige_score,
            achievement_score=achievement_score,
            blocks=blocks,
        )

        # 4b. Explicit Domain Alignment & Context Blending
        s_domain, beta_domain = calculate_domain_score(
            persona=persona,
            blocks=blocks,
            job=job,
            candidate_domain_profile=candidate_domain_profile,
        )
        s_context = (1.0 - beta_domain) * s_archetype + beta_domain * s_domain

        # 5. Compensation Normalization & Feasibility (0.10 weight)
        s_comp = calculate_compensation_score(
            persona_min_salary=persona.min_salary,
            job=job,
        )

        # 6. Posting Freshness Advantage (0.10 weight)
        s_freshness = calculate_freshness_score(job.posted_at, job.created_at)

        # 7. Bayesian Uncertainty Gate
        g_prob, hard_pass, gate_notes = calculate_probabilistic_gate(
            candidate_visa=account.visa_status,
            job_visa=job.visa_sponsorship,
            candidate_locations=account.preferred_locations,
            candidate_remote=account.remote_preference,
            job_location=job.raw_location,
            job_workplace=job.workplace_type,
            job_country_code=job.country_code,
        )

        # 8. Unified Master Reranking Equation
        # P(Match) = (G_prob * D_core) * [
        #     0.25*S_skills + 0.25*S_sem + 0.15*S_sen
        #     + 0.15*S_context + 0.10*S_comp + 0.10*S_fresh
        # ]
        weighted_core = (
            (0.25 * s_skills)
            + (0.25 * s_semantic)
            + (0.15 * s_seniority)
            + (0.15 * s_context)
            + (0.10 * s_comp)
            + (0.10 * s_freshness)
        )
        p_match = round((g_prob * d_core) * weighted_core, 4)

        if p_match < min_score:
            continue

        # Classify probability band
        if p_match >= 0.75:
            band = "high"
        elif p_match >= 0.50:
            band = "moderate"
        else:
            band = "low"

        breakdown = MatchFactorBreakdown(
            g_prob=round(g_prob, 2),
            skill_score=round(s_skills, 2),
            semantic_score=round(s_semantic, 2),
            seniority_score=round(s_seniority, 2),
            prestige_booster=round(prestige_score, 2),
            achievement_booster=round(achievement_score, 2),
            freshness_booster=round(s_freshness, 2),
            d_core=round(d_core, 2),
            archetype_score=round(s_archetype, 2),
            domain_score=round(s_domain, 2),
            context_score=round(s_context, 2),
            comp_score=round(s_comp, 2),
        )

        result_item = JobMatchResult(
            job_id=str(job.id),
            title=job.title,
            company_name=job.company_name,
            location=job.raw_location,
            workplace_type=job.workplace_type,
            salary_range=job.salary_range,
            visa_sponsorship=job.visa_sponsorship,
            apply_url=job.apply_url or job.url,
            posted_at=job.posted_at,
            match_score=p_match,
            hard_gate_pass=hard_pass,
            probability_band=band,
            breakdown=breakdown,
            matched_skills=matched_s[:8],
            missing_dealbreakers=missing_s[:5],
            phrasing_equivalents=equivs[:3],
            gate_notes=gate_notes,
        )
        scored_results.append(result_item)

        # 9. Update JobMatchCache in PostgreSQL asynchronously
        cache_stmt = select(JobMatchCache).where(
            JobMatchCache.persona_id == persona.id,
            JobMatchCache.job_listing_id == job.id,
        )
        cache_res = await db.execute(cache_stmt)
        existing_cache = cache_res.scalar_one_or_none()

        if existing_cache is None:
            new_cache = JobMatchCache(
                id=uuid.uuid4(),
                persona_id=persona.id,
                job_listing_id=job.id,
                match_score=p_match,
                hard_gate_pass=hard_pass,
                skill_overlap_score=s_skills,
                semantic_score=s_semantic,
                seniority_score=s_seniority,
                prestige_booster=prestige_score,
                achievement_booster=achievement_score,
                missing_skills=missing_s,
                matched_skills=matched_s,
                d_core=d_core,
                archetype_score=s_archetype,
                domain_score=s_domain,
                context_score=s_context,
                comp_score=s_comp,
                freshness_score=s_freshness,
                evaluated_at=datetime.now(UTC),
            )
            db.add(new_cache)
        else:
            existing_cache.match_score = p_match
            existing_cache.hard_gate_pass = hard_pass
            existing_cache.skill_overlap_score = s_skills
            existing_cache.semantic_score = s_semantic
            existing_cache.seniority_score = s_seniority
            existing_cache.prestige_booster = prestige_score
            existing_cache.achievement_booster = achievement_score
            existing_cache.missing_skills = missing_s
            existing_cache.matched_skills = matched_s
            existing_cache.d_core = d_core
            existing_cache.archetype_score = s_archetype
            existing_cache.domain_score = s_domain
            existing_cache.context_score = s_context
            existing_cache.comp_score = s_comp
            existing_cache.freshness_score = s_freshness
            existing_cache.evaluated_at = datetime.now(UTC)

    await db.commit()

    # Dynamic sorting: By date (newest first) or by acceptance probability
    # score descending
    if sort_by == "date":
        min_dt = datetime.min.replace(tzinfo=UTC)

        def _sort_date_key(r: JobMatchResult) -> tuple[datetime, float]:
            dt = r.posted_at
            if dt is None:
                dt_clean = min_dt
            elif dt.tzinfo is None:
                dt_clean = dt.replace(tzinfo=UTC)
            else:
                dt_clean = dt
            return (dt_clean, r.match_score)

        scored_results.sort(key=_sort_date_key, reverse=True)
    else:
        scored_results.sort(key=lambda r: r.match_score, reverse=True)

    total_count = len(scored_results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = scored_results[start_idx:end_idx]

    return paginated_results, total_count
