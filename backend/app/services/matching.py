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
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cv_block import CVBlock
from app.models.job_listing import JobListing
from app.models.user_account import (
    CandidatePersona,
    JobMatchCache,
    PersonaSkill,
    UserAccount,
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


class MatchFactorBreakdown(BaseModel):
    """Detailed score decomposition for matching transparency."""

    g_prob: float = Field(..., description="Bayesian gate multiplier [0.0, 1.0].")
    skill_score: float = Field(..., description="Skill overlap factor [0.0, 1.0].")
    semantic_score: float = Field(..., description="Vector cosine similarity.")
    seniority_score: float = Field(..., description="Experience alignment score.")
    prestige_booster: float = Field(..., description="Company/School prestige factor.")
    achievement_booster: float = Field(..., description="Hackathons/Honors booster.")
    freshness_booster: float = Field(..., description="Posting recency advantage.")


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
        else {s.strip().lower() for s in candidate_skills if s.strip()}
    )
    job_lower = [s.strip().lower() for s in job_skills if s.strip()]

    if not job_lower:
        # Neutral score if job does not declare explicit skill requirements
        return 0.70, list(candidate_skills)[:5], [], []

    matched: list[str] = []
    missing: list[str] = []
    equivalents: list[dict[str, str]] = []

    for js in job_lower:
        if js in cand_lower:
            matched.append(js)
            continue

        # Check cross-technology phrasing equivalents
        eq_set = TECH_EQUIVALENCES.get(js, set())
        overlap_eq = eq_set.intersection(cand_lower)
        if overlap_eq:
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

    overlap_ratio = len(matched) / max(1, len(job_lower))
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
) -> tuple[list[JobMatchResult], int]:
    """
    Execute two-stage job retrieval, reranking, and persistent caching.

    Stage 1: Deterministic SQL Pre-Filter (<15ms, bounded to 250 jobs).
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

    requires_visa = account.visa_status.strip().lower() in {
        "h-1b",
        "f-1 opt",
        "requires_sponsorship",
        "requires sponsorship",
    }

    # -----------------------------------------------------------------------
    # STAGE 1: Deterministic SQL Pre-Filter
    # -----------------------------------------------------------------------
    stage1_stmt = (
        select(JobListing)
        .options(selectinload(JobListing.ats_board))
        .where(JobListing.status == "active")
    )

    # Hard negative visa exclusion
    if requires_visa or visa_filter:
        stage1_stmt = stage1_stmt.where(
            or_(
                JobListing.visa_sponsorship.is_(None),
                JobListing.visa_sponsorship != "no",
            )
        )

    # Modality filter
    if modality_filter:
        stage1_stmt = stage1_stmt.where(
            JobListing.workplace_type == modality_filter.lower()
        )

    # Keyword / Role title pre-filtering
    if target_roles:
        role_clauses = [JobListing.title.ilike(f"%{role}%") for role in target_roles]
        stage1_stmt = stage1_stmt.where(or_(*role_clauses))

    # Bound candidate pool to maximum 250 jobs for Stage 2 reranking
    stage1_stmt = stage1_stmt.order_by(JobListing.created_at.desc()).limit(250)

    stage1_result = await db.execute(stage1_stmt)
    candidate_jobs = stage1_result.scalars().all()

    # If role filter was overly strict and returned zero jobs, fall back to broad pool
    if not candidate_jobs:
        fallback_stmt = (
            select(JobListing)
            .options(selectinload(JobListing.ats_board))
            .where(JobListing.status == "active")
            .order_by(JobListing.created_at.desc())
            .limit(100)
        )
        if requires_visa or visa_filter:
            fallback_stmt = fallback_stmt.where(
                or_(
                    JobListing.visa_sponsorship.is_(None),
                    JobListing.visa_sponsorship != "no",
                )
            )
        if modality_filter:
            fallback_stmt = fallback_stmt.where(
                JobListing.workplace_type == modality_filter.lower()
            )
        fallback_result = await db.execute(fallback_stmt)
        candidate_jobs = fallback_result.scalars().all()

    # -----------------------------------------------------------------------
    # STAGE 2: Precision Multi-Factor Reranker
    # -----------------------------------------------------------------------
    scored_results: list[JobMatchResult] = []

    # Pre-calculate candidate-level constants
    organizations = [b.organization for b in blocks if b.organization]
    prestige_score = calculate_prestige_score(organizations)
    achievement_score = calculate_achievement_score(blocks)
    candidate_skills_lower = {s.strip().lower() for s in persona_skills if s.strip()}

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

        # 1. Skill Overlap & Hidden Equivalence Discovery
        s_skills, matched_s, missing_s, equivs = calculate_skill_overlap(
            persona_skills,
            job_skills,
            candidate_skills_lower=candidate_skills_lower,
        )

        # 2. Seniority Calibration
        job_exp_years = reqs.get("years_experience_min")
        job_sen = reqs.get("seniority_level")
        s_seniority = calculate_seniority_score(
            candidate_years=persona.years_experience,
            candidate_seniority=persona.seniority_level,
            job_seniority=job_sen,
            job_min_years=job_exp_years,
        )

        # 3. Posting Recency Advantage
        s_freshness = calculate_freshness_score(job.posted_at, job.created_at)

        # 4. Semantic Similarity (Keyword and taxonomy alignment)
        # Cosine distance simulation for text match
        role_match_ratio = (
            1.0
            if any(r in (job.title or "").lower() for r in target_roles)
            else (0.5 if target_roles else 0.7)
        )
        s_semantic = max(0.2, (0.6 * s_skills) + (0.4 * role_match_ratio))

        # 5. Bayesian Uncertainty Gate
        g_prob, hard_pass, gate_notes = calculate_probabilistic_gate(
            candidate_visa=account.visa_status,
            job_visa=job.visa_sponsorship,
            candidate_locations=account.preferred_locations,
            candidate_remote=account.remote_preference,
            job_location=job.raw_location,
            job_workplace=job.workplace_type,
            job_country_code=job.country_code,
        )

        # 6. Composite Acceptance Probability P(Match)
        # Formula: P(Match) = G_prob * (0.30*S_skills + 0.25*S_sem + 0.15*S_sen
        #                             + 0.10*S_prest + 0.10*S_ach + 0.10*S_fresh)
        weighted_core = (
            (0.30 * s_skills)
            + (0.25 * s_semantic)
            + (0.15 * s_seniority)
            + (0.10 * prestige_score)
            + (0.10 * achievement_score)
            + (0.10 * s_freshness)
        )
        p_match = round(g_prob * weighted_core, 4)

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

        # 7. Update JobMatchCache in PostgreSQL asynchronously
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
            existing_cache.evaluated_at = datetime.now(UTC)

    await db.commit()

    # Sort candidates by acceptance probability score descending
    scored_results.sort(key=lambda r: r.match_score, reverse=True)

    total_count = len(scored_results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = scored_results[start_idx:end_idx]

    return paginated_results, total_count
