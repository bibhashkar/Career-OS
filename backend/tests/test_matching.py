"""
Unit and integration tests for Two-Stage Matching Engine & Three-Tier Diagnostics.

Validates:
  - ADR-008 mathematical scoring models (prestige, achievement, freshness,
    skill overlap).
  - Bayesian uncertainty gate (missing visa parameters get 0.85 discount, not 0.0).
  - End-to-end two-stage retrieval & ranking pipeline.
  - Tier 0 360° candidate holistic audit API.
  - Tier 1 per-job diagnostic API.
  - Tier 2 persona market benchmark API.
"""

import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.tools.embeddings import generate_deterministic_embedding
from app.core.auth import create_access_token
from app.core.database import get_db
from app.ingestion.deterministic_extractor import (
    classify_industry_vertical,
    extract_domain_strictness,
)
from app.main import app
from app.models.cv_block import CVBlock
from app.models.ingestion import ATSBoard, ATSProvider, IndustrySector
from app.models.job_listing import JobListing
from app.models.user_account import CandidatePersona, PersonaSkill, UserAccount
from app.services.matching import (
    calculate_achievement_score,
    calculate_archetype_score,
    calculate_compensation_score,
    calculate_domain_score,
    calculate_freshness_score,
    calculate_match_upgraded,
    calculate_prestige_score,
    calculate_probabilistic_gate,
    calculate_semantic_top3_score,
    calculate_seniority_score,
    calculate_skill_overlap,
    normalize_job_compensation,
    retrieve_stage1_candidates,
)


def test_calculate_prestige_score() -> None:
    """Verify prestige classification across Tier 1, Tier 2, and unlisted orgs."""
    # Tier 1 FAANG / Top Quant / Top CS universities
    assert calculate_prestige_score(["Google", "Meta"]) == 1.0
    assert calculate_prestige_score(["Jane Street"]) == 1.0
    assert calculate_prestige_score(["Stanford University"]) == 1.0
    assert calculate_prestige_score(["OpenAI"]) == 1.0

    # Tier 2 public tech / scaleups
    assert calculate_prestige_score(["Spotify"]) == 0.8
    assert calculate_prestige_score(["Atlassian"]) == 0.8
    assert calculate_prestige_score(["Georgia Tech"]) == 0.8

    # Unlisted standard enterprise / baseline
    assert calculate_prestige_score(["Acme Regional Services"]) == 0.5
    assert calculate_prestige_score([]) == 0.3


def test_calculate_achievement_score() -> None:
    """Verify distinction scoring for hackathon placements and open-source stars."""
    # 1st Place Hackathon Block
    hack_block = CVBlock(
        category="hackathon_achievement",
        title="1st Place Winner - AI Infra Track",
        content="Won grand prize building autonomous LangGraph scheduler.",
        metrics={"placement": "1st Place", "competitors": 1200},
    )
    assert calculate_achievement_score([hack_block]) == 1.0

    # Open Source Block with 600+ stars
    oss_block = CVBlock(
        category="open_source",
        title="Core Maintainer",
        content="Maintained async task worker in Go and Kafka.",
        metrics={"github_stars": 650},
    )
    assert calculate_achievement_score([oss_block]) == 1.0

    # Baseline experience block without competition distinction
    standard_block = CVBlock(
        category="work_experience",
        title="Backend Engineer",
        content="Built CRUD REST endpoints in Django.",
        metrics={},
    )
    assert calculate_achievement_score([standard_block]) == 0.2


def test_calculate_freshness_score() -> None:
    """Verify decay scoring reflecting the 3.8x recruiter callback rate window."""
    now = datetime.now(UTC)

    # 1 day old (<= 3 days) -> 1.0
    posted_1d = now - timedelta(days=1)
    assert calculate_freshness_score(posted_1d, None) == 1.0

    # 7 days old (<= 14 days) -> 0.75
    posted_7d = now - timedelta(days=7)
    assert calculate_freshness_score(posted_7d, None) == 0.75

    # 20 days old (<= 30 days) -> 0.45
    posted_20d = now - timedelta(days=20)
    assert calculate_freshness_score(posted_20d, None) == 0.45

    # 45 days old (> 30 days) -> 0.15
    posted_45d = now - timedelta(days=45)
    assert calculate_freshness_score(posted_45d, None) == 0.15


def test_calculate_skill_overlap_and_hidden_equivalents() -> None:
    """Verify cross-technology equivalence discovery (e.g. GCP -> AWS)."""
    candidate_skills = {"Python", "FastAPI", "GCP", "PostgreSQL", "Docker"}
    job_skills = ["python", "fastapi", "aws", "postgresql", "kubernetes"]

    ratio, matched, missing, equivs = calculate_skill_overlap(
        candidate_skills, job_skills
    )

    assert "python" in matched
    assert "fastapi" in matched
    assert "postgresql" in matched
    # AWS should be matched via GCP equivalence
    assert "aws" in matched
    assert any(
        eq["job_term"] == "Aws" and eq["candidate_has"] == "Gcp" for eq in equivs
    )
    # Kubernetes matched via Docker equivalence
    assert "kubernetes" in matched
    assert ratio >= 0.80


def test_calculate_seniority_score() -> None:
    """Verify seniority calibration and required years alignment."""
    # Senior candidate vs Senior role
    score_exact = calculate_seniority_score(
        candidate_years=6,
        candidate_seniority="senior",
        job_seniority="senior",
        job_min_years=5,
    )
    assert score_exact >= 0.90

    # Junior candidate vs Senior role (under-tenured penalty)
    score_under = calculate_seniority_score(
        candidate_years=1,
        candidate_seniority="junior",
        job_seniority="senior",
        job_min_years=5,
    )
    assert score_under <= 0.40


def test_calculate_probabilistic_gate_bayesian_uncertainty() -> None:
    """
    Critical ADR-002 verification:
    Missing visa sponsorship MUST NOT result in 0.0 (hard failure).
    It must receive the 0.85 Bayesian uncertainty discount.
    """
    # Case 1: Candidate needs visa, job explicitly says 'no' -> 0.0 Hard Gate Failure
    g_no, pass_no, _ = calculate_probabilistic_gate(
        candidate_visa="H-1B",
        job_visa="no",
        candidate_locations=["San Francisco, CA"],
        candidate_remote="Remote",
        job_location="Remote",
        job_workplace="remote",
        job_country_code="US",
    )
    assert g_no == 0.0
    assert pass_no is False

    # Case 2: Candidate needs visa, job has NULL / unspecified -> 0.85 Discount
    g_null, pass_null, notes_null = calculate_probabilistic_gate(
        candidate_visa="H-1B",
        job_visa=None,
        candidate_locations=["San Francisco, CA"],
        candidate_remote="Remote",
        job_location="Remote",
        job_workplace="remote",
        job_country_code="US",
    )
    assert g_null == 0.85
    assert pass_null is True
    assert any("uncertainty discount" in n.lower() for n in notes_null)

    # Case 3: Candidate needs visa, job verified 'yes' -> 1.0 Full Pass
    g_yes, pass_yes, _ = calculate_probabilistic_gate(
        candidate_visa="H-1B",
        job_visa="yes",
        candidate_locations=["San Francisco, CA"],
        candidate_remote="Remote",
        job_location="Remote",
        job_workplace="remote",
        job_country_code="US",
    )
    assert g_yes == 1.0
    assert pass_yes is True

    # Case 4: Candidate is US Citizen (does not need visa) -> 1.0 Full Pass
    g_cit, pass_cit, _ = calculate_probabilistic_gate(
        candidate_visa="Citizen",
        job_visa="no",  # Even if job says no sponsorship, citizen passes
        candidate_locations=["San Francisco, CA"],
        candidate_remote="Remote",
        job_location="Remote",
        job_workplace="remote",
        job_country_code="US",
    )
    assert g_cit == 1.0
    assert pass_cit is True


@pytest.mark.asyncio
async def test_job_matching_and_diagnostics_api_flow(
    db_session: AsyncSession,
) -> None:
    """
    Integration test verifying /api/jobs/matches, Tier 0 Audit, and Tier 1 Diagnostics.
    """
    engine = db_session.bind
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    try:
        # Seed auxiliary tables required for foreign keys
        user_uuid = uuid.uuid4()
        persona_uuid = uuid.uuid4()
        board_uuid = uuid.uuid4()
        job1_uuid = uuid.uuid4()
        job2_uuid = uuid.uuid4()

        async with session_maker() as session:
            # 1. ATS Provider & Industry Sector
            provider = ATSProvider(
                code="greenhouse",
                name="Greenhouse",
                api_base_url="https://boards-api.greenhouse.io/v1",
                auth_type="public_api",
                default_rate_limit_rps=5.0,
                is_active=True,
            )
            industry = IndustrySector(
                code="technology_software",
                name="Technology & Software",
                description="Core software",
                is_active=True,
            )
            board = ATSBoard(
                id=board_uuid,
                provider="greenhouse",
                slug="stripe",
                company_name="Stripe",
                tier=1,
                priority=10,
                is_active=True,
            )
            session.add_all([provider, industry, board])
            await session.flush()

            # 2. Candidate Account & Universal Persona
            account = UserAccount(
                id=user_uuid,
                email="candidate.matching@example.com",
                full_name="Sarah Architect",
                visa_status="H-1B",
                citizenship_country_code="US",
                preferred_locations=["San Francisco, CA", "Remote"],
                remote_preference="Remote",
                is_active=True,
            )
            persona = CandidatePersona(
                id=persona_uuid,
                user_account_id=user_uuid,
                name="AI Platform Engineer",
                is_common_persona=True,
                is_default=True,
                headline="Distributed AI Systems Architect",
                target_roles=["AI Platform Engineer", "Backend Engineer"],
                target_industries=["technology_software"],
                years_experience=6,
                seniority_level="senior",
            )
            session.add_all([account, persona])
            await session.flush()

            # 3. Candidate Skills
            for s in ["Python", "FastAPI", "Kafka", "PostgreSQL", "Docker"]:
                session.add(
                    PersonaSkill(
                        id=uuid.uuid4(),
                        persona_id=persona_uuid,
                        skill_name=s,
                        category="tool",
                        proficiency="expert",
                        years_experience=5,
                        is_core=True,
                    )
                )

            # 4. Candidate CV Block with verified metrics and Tier 1 pedigree
            block = CVBlock(
                id=uuid.uuid4(),
                user_account_id=user_uuid,
                category="hackathon_achievement",
                title="1st Place Winner - Distributed AI Track",
                organization="Google",
                content=(
                    "Built low-latency model inference scheduler in Python and Kafka. "
                    "Decreased p99 latency by 45% under 100k req/s load."
                ),
                metrics={
                    "placement": "1st Place",
                    "percentage_impact": "45%",
                    "throughput_or_latency": "100k req/s",
                },
                skills=["Python", "Kafka", "FastAPI"],
            )
            session.add(block)

            # 5. Job Listings (Job 1: High match, Job 2: Negative visa exclusion)
            job_high = JobListing(
                id=job1_uuid,
                title="Senior AI Platform Engineer",
                company_name="Stripe",
                ats_board_id=board_uuid,
                ats_provider="greenhouse",
                ats_board_slug="stripe",
                source_job_id="str-101",
                industry="technology_software",
                raw_location="San Francisco, CA",
                city="San Francisco",
                state_province="California",
                state_province_code="CA",
                country="United States",
                country_code="US",
                primary_region="north_america",
                workplace_type="remote",
                salary_range="$190,000 - $240,000",
                raw_description="Build real-time event streaming systems with Python.",
                ats_requirements={
                    "hard_skills": ["Python", "FastAPI", "Kafka", "PostgreSQL"],
                    "seniority_level": "senior",
                    "years_experience_min": 5,
                },
                visa_sponsorship="yes",
                status="active",
                posted_at=datetime.now(UTC) - timedelta(days=2),
            )
            job_no_visa = JobListing(
                id=job2_uuid,
                title="Backend Engineer",
                company_name="Regional Corp",
                ats_board_id=board_uuid,
                ats_provider="greenhouse",
                ats_board_slug="stripe",
                source_job_id="reg-102",
                industry="technology_software",
                raw_location="San Francisco, CA",
                workplace_type="on_site",
                salary_range="$140,000 - $160,000",
                raw_description="Backend tasks.",
                ats_requirements={"hard_skills": ["Java"]},
                visa_sponsorship="no",  # Should be excluded in Stage 1
                status="active",
                posted_at=datetime.now(UTC) - timedelta(days=25),
            )
            session.add_all([job_high, job_no_visa])
            await session.commit()

        # Execute API requests
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = create_access_token(
                user_id=str(user_uuid),
                email="candidate.matching@example.com",
            )
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Test /api/jobs/matches (Two-Stage Ranking)
            matches_resp = await client.get("/api/jobs/matches", headers=headers)
            assert matches_resp.status_code == 200
            data = matches_resp.json()
            assert data["persona_name"] == "AI Platform Engineer"
            assert data["total_count"] >= 1
            top_match = data["jobs"][0]
            assert top_match["title"] == "Senior AI Platform Engineer"
            assert top_match["probability_band"] == "high"
            assert top_match["match_score"] >= 0.75
            assert top_match["hard_gate_pass"] is True
            assert "Python" in [s.title() for s in top_match["matched_skills"]]

            # Verify Job 2 (visa='no') was excluded for H-1B candidate
            assert not any(j["job_id"] == str(job2_uuid) for j in data["jobs"])

            # 1b. Test search keyword filtering (company/title)
            q_match = await client.get("/api/jobs/matches?q=Stripe", headers=headers)
            assert q_match.status_code == 200
            assert q_match.json()["total_count"] >= 1

            q_miss = await client.get(
                "/api/jobs/matches?q=NonexistentCompany", headers=headers
            )
            assert q_miss.status_code == 200
            assert q_miss.json()["total_count"] == 0

            # 1c. Test city/state/region location filtering
            loc_match = await client.get(
                "/api/jobs/matches?location=San+Francisco", headers=headers
            )
            assert loc_match.status_code == 200
            assert loc_match.json()["total_count"] >= 1

            loc_miss = await client.get(
                "/api/jobs/matches?location=Tokyo", headers=headers
            )
            assert loc_miss.status_code == 200
            assert loc_miss.json()["total_count"] == 0

            # 1d. Test posted_within recency filtering
            date_miss = await client.get(
                "/api/jobs/matches?posted_within=1", headers=headers
            )
            assert date_miss.status_code == 200
            assert date_miss.json()["total_count"] == 0

            date_hit = await client.get(
                "/api/jobs/matches?posted_within=7", headers=headers
            )
            assert date_hit.status_code == 200
            assert date_hit.json()["total_count"] >= 1

            # 1e. Test sorting by date
            sort_date = await client.get(
                "/api/jobs/matches?sort_by=date", headers=headers
            )
            assert sort_date.status_code == 200
            assert sort_date.json()["total_count"] >= 1

            # 2. Test /api/jobs/{job_id}/diagnostics (Tier 1 Breakdown)
            diag_resp = await client.get(
                f"/api/jobs/{job1_uuid}/diagnostics?persona_id={persona_uuid}",
                headers=headers,
            )
            assert diag_resp.status_code == 200
            diag_data = diag_resp.json()
            assert diag_data["job_id"] == str(job1_uuid)
            assert diag_data["probability_band"] == "high"
            assert "Verified" in diag_data["visa_status_message"]

            # 3. Test /api/candidates/audit (Tier 0 Holistic Audit)
            audit_resp = await client.get("/api/candidates/audit", headers=headers)
            assert audit_resp.status_code == 200
            audit_data = audit_resp.json()
            assert audit_data["candidate_name"] == "Sarah Architect"
            assert audit_data["market_percentile"] >= 75
            assert audit_data["quantified_impact_ratio"] == 1.0
            assert any(
                b["code"] == "hackathon_winner" and b["verified"]
                for b in audit_data["distinction_badges"]
            )
            assert any(
                b["code"] == "tier1_pedigree" and b["verified"]
                for b in audit_data["distinction_badges"]
            )

            # 4. Test /api/candidates/personas/{persona_id}/benchmark (Tier 2 Benchmark)
            bench_resp = await client.get(
                f"/api/candidates/personas/{persona_uuid}/benchmark",
                headers=headers,
            )
            assert bench_resp.status_code == 200
            bench_data = bench_resp.json()
            assert bench_data["persona_name"] == "AI Platform Engineer"
            assert bench_data["analyzed_jobs_count"] >= 1
            assert len(bench_data["top_market_skills"]) >= 1

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_semantic_vector_top3_max_sim_no_double_counting() -> None:
    """
    Verify S_semantic uses vector cosine similarity over CVBlock embeddings.

    Ensures that when jobs have identical skills declared, the semantic score
    discriminates accurately based on actual content embeddings rather than
    merely repeating S_skills (eliminating the double-counting bug).
    """
    # Candidate with distributed AI infra achievement block
    block_text = (
        "Optimized high-throughput tensor parallel model inference "
        "with Python and CUDA."
    )
    block = CVBlock(
        title="Distributed Model Inference",
        content=block_text,
        embedding=generate_deterministic_embedding(block_text),
    )

    # Job A: Distributed AI Infra (high semantic similarity)
    job_ai_text = (
        "AI Infrastructure Engineer Build distributed inference "
        "pipelines and GPU tensor."
    )
    job_ai = JobListing(
        title="AI Infrastructure Engineer",
        raw_description=job_ai_text,
        ats_requirements={"hard_skills": ["Python"]},
        embedding=generate_deterministic_embedding(job_ai_text),
    )

    # Job B: Frontend Web (low semantic similarity, despite sharing 'Python' skill)
    job_fe_text = (
        "Frontend Web Developer Design user interfaces in React, HTML, CSS with Python."
    )
    job_fe = JobListing(
        title="Frontend Web Developer",
        raw_description=job_fe_text,
        ats_requirements={"hard_skills": ["Python"]},
        embedding=generate_deterministic_embedding(job_fe_text),
    )

    target_roles = ["AI Infrastructure Engineer"]
    score_ai = calculate_semantic_top3_score([block], job_ai, target_roles)
    score_fe = calculate_semantic_top3_score([block], job_fe, target_roles)

    # Semantic score for AI job must significantly exceed frontend job
    assert score_ai > score_fe
    assert score_ai >= 0.45
    assert score_fe < 0.30


def test_compensation_normalization_and_exponential_penalty() -> None:
    """
    Verify salary extraction, prevailing wage fallback, and exponential penalty.
    """
    # 1. Explicit bounds
    job_explicit = JobListing(
        title="Senior Engineer",
        salary_min=180000,
        salary_max=220000,
        salary_currency="USD",
        is_salary_estimated=False,
        raw_description="Senior roles.",
    )
    c_min, c_max, is_est = normalize_job_compensation(job_explicit)
    assert c_min == 180000
    assert c_max == 220000
    assert is_est is False

    # 2. String parsing from salary_range
    job_str1 = JobListing(
        title="Staff Engineer",
        salary_range="$190,000 - $240,000",
        raw_description="Staff roles.",
    )
    _, max1, est1 = normalize_job_compensation(job_str1)
    assert max1 == 240000
    assert est1 is False

    job_str2 = JobListing(
        title="Mid Engineer",
        salary_range="$140k - $160k",
        raw_description="Mid roles.",
    )
    _, max2, est2 = normalize_job_compensation(job_str2)
    assert max2 == 160000
    assert est2 is False

    # 3. Prevailing wage fallback for undisclosed compensation
    job_undisclosed = JobListing(
        title="Senior Engineer",
        salary_range=None,
        ats_requirements={"seniority_level": "senior"},
        industry="technology_software",
        raw_description="Senior roles.",
    )
    _, max_undisc, est_undisc = normalize_job_compensation(job_undisclosed)
    assert max_undisc > 150000
    assert est_undisc is True

    # 4. Feasibility scores:
    # No min salary declared -> 1.0
    assert calculate_compensation_score(None, job_str1) == 1.0
    assert calculate_compensation_score(0, job_str1) == 1.0

    # Salary target met ($200k target vs $240k max) -> 1.0
    assert calculate_compensation_score(200000, job_str1) == 1.0

    # Salary target unmet ($200k target vs $160k max):
    # shortfall = (200k - 160k) / 200k = 0.20
    # exp(-3.0 * 0.20) = exp(-0.60) ~= 0.5488
    score_unmet = calculate_compensation_score(200000, job_str2)
    assert 0.50 <= score_unmet <= 0.60


def test_archetype_alignment_job_variance() -> None:
    """
    Verify S_archetype produces job-discriminating scores across company archetypes.

    Candidate has Tier 1 pedigree and high-scale low-latency proof, but modest OSS.
    HFT Quant and Tier 1 Scaleup jobs must score higher than an OSS DevTools role.
    """
    block_scale = CVBlock(
        category="work_experience",
        title="Core Infrastructure Engineer",
        organization="Google",
        content=(
            "Engineered low latency cache. Decreased p99 latency under 200k req/s."
        ),
        metrics={"throughput_or_latency": "200k req/s", "p99": "2ms"},
    )

    prestige = 1.0  # Google pedigree
    achievement = 0.20  # Standard achievement baseline

    job_hft = JobListing(
        title="Quant Systems Engineer",
        company_name="Citadel",
        industry="hft_quant_trading",
        raw_description="Ultra low latency C++ trading systems with microsecond scale.",
    )

    job_oss = JobListing(
        title="Open Source Developer Advocate",
        company_name="DevCommunity",
        industry="devtools",
        raw_description="Maintain public open source community repos and sdks.",
    )

    score_hft = calculate_archetype_score(job_hft, prestige, achievement, [block_scale])
    score_oss = calculate_archetype_score(job_oss, prestige, achievement, [block_scale])

    # HFT rewards candidate's pedigree and scale proof; OSS role scores lower
    assert score_hft > score_oss
    assert score_hft >= 0.70
    assert score_oss < 0.55


@pytest.mark.asyncio
async def test_stage1_rrf_prevents_recency_starvation(
    db_session: AsyncSession,
) -> None:
    """
    Verify Stage 1 RRF retrieves older, high-match jobs even when newer
    low-relevance jobs fill the catalog (defeating recency starvation).
    """
    user_uuid = uuid.uuid4()
    persona_uuid = uuid.uuid4()
    board_uuid = uuid.uuid4()

    provider = ATSProvider(
        code="greenhouse_rrf",
        name="Greenhouse RRF",
        api_base_url="https://boards-api.greenhouse.io/v1",
        auth_type="public_api",
        default_rate_limit_rps=5.0,
        is_active=True,
    )
    board = ATSBoard(
        id=board_uuid,
        provider="greenhouse_rrf",
        slug="techcorp",
        company_name="TechCorp",
        tier=1,
        priority=10,
        is_active=True,
    )
    account = UserAccount(
        id=user_uuid,
        email="rrf.test@example.com",
        full_name="Alex RRF",
        visa_status="Citizen",
        preferred_locations=["Remote"],
        remote_preference="Remote",
        is_active=True,
    )
    persona = CandidatePersona(
        id=persona_uuid,
        user_account_id=user_uuid,
        name="Distributed Systems Specialist",
        is_common_persona=True,
        is_default=True,
        headline="Distributed Systems Specialist",
        target_roles=["Distributed Systems Engineer"],
        years_experience=5,
        seniority_level="senior",
    )
    db_session.add_all([provider, board, account, persona])
    await db_session.flush()

    now = datetime.now(UTC)

    # 1. Older High-Match Job (posted 25 days ago)
    old_high_match_id = uuid.uuid4()
    old_high_job = JobListing(
        id=old_high_match_id,
        title="Senior Distributed Systems Engineer",
        company_name="TechCorp",
        ats_board_id=board_uuid,
        ats_provider="greenhouse_rrf",
        ats_board_slug="techcorp",
        source_job_id="dist-old-1",
        industry="technology_software",
        raw_location="Remote",
        workplace_type="remote",
        raw_description="Build distributed consensus and Kafka streaming systems.",
        ats_requirements={"hard_skills": ["Kafka", "Python", "Kubernetes"]},
        status="active",
        posted_at=now - timedelta(days=25),
        created_at=now - timedelta(days=25),
    )
    db_session.add(old_high_job)

    # 2. Ten Newer Irrelevant Jobs (posted 1 hour ago)
    for i in range(10):
        new_job = JobListing(
            id=uuid.uuid4(),
            title=f"Marketing Assistant {i}",
            company_name="Retail Brand",
            ats_board_id=board_uuid,
            ats_provider="greenhouse_rrf",
            ats_board_slug="techcorp",
            source_job_id=f"mkt-{i}",
            industry="technology_software",
            raw_location="Remote",
            workplace_type="remote",
            raw_description="Social media and flyer designs.",
            ats_requirements={"hard_skills": ["Photoshop", "Canva"]},
            status="active",
            posted_at=now - timedelta(hours=i + 1),
            created_at=now - timedelta(hours=i + 1),
        )
        db_session.add(new_job)

    await db_session.commit()

    candidate_skills = {"kafka", "python", "kubernetes"}
    candidate_skills_lower = {"kafka", "python", "kubernetes"}

    # Retrieve candidates bounded to limit 5
    retrieved = await retrieve_stage1_candidates(
        db=db_session,
        persona=persona,
        account=account,
        blocks=[],
        persona_skills=candidate_skills,
        candidate_skills_lower=candidate_skills_lower,
        limit=5,
    )

    retrieved_ids = [j.id for j in retrieved]
    # The older, highly relevant job MUST be in the top 5 retrieved candidates
    assert old_high_match_id in retrieved_ids


def test_classify_industry_vertical_and_strictness() -> None:
    """Verify deterministic industry classification and domain strictness extraction."""
    # 1. HealthTech strict
    ht_desc = "Build HIPAA-compliant claims engine with EDI 837 and FHIR pipelines."
    ht_vertical = classify_industry_vertical(
        title="Senior Platform Engineer",
        raw_description=ht_desc,
        company_name="Optum",
    )
    assert ht_vertical == "healthtech"
    ht_strictness = extract_domain_strictness(
        title="Senior Platform Engineer",
        raw_description=ht_desc,
        industry_vertical=ht_vertical,
    )
    assert ht_strictness == 1.0

    # 2. Gaming
    gaming_vertical = classify_industry_vertical(
        title="Gameplay Backend Engineer",
        raw_description="Unreal Engine and multiplayer game server matchmaking.",
        company_name="Riot Games",
    )
    assert gaming_vertical == "gaming"

    # 3. Domain-agnostic SaaS
    saas_vertical = classify_industry_vertical(
        title="Senior Backend Engineer",
        raw_description="Build microservices using Python, FastAPI, and PostgreSQL.",
        company_name="Acme Inc",
    )
    assert saas_vertical == "general_saas"
    saas_strictness = extract_domain_strictness(
        title="Senior Backend Engineer",
        raw_description="Build microservices using Python, FastAPI, and PostgreSQL.",
        industry_vertical=saas_vertical,
    )
    assert saas_strictness == 0.0


def test_domain_tenure_bonus_curve() -> None:
    """
    Verify piecewise linear saturating tenure bonus curve:
    TenureBonus(YoE) = min(1.0, 0.50 + 0.10 * min(YoE, 5) + 0.02 * max(0, YoE - 5))
    """
    job = JobListing(
        title="HealthTech Backend Engineer",
        company_name="Optum",
        industry_vertical="healthtech",
        domain_strictness=1.0,
        raw_description="HIPAA EDI 837 required",
    )

    # 0 YoE
    p0 = CandidatePersona(
        name="Zero Domain",
        years_experience=5,
        seniority_level="mid",
    )
    b0 = [
        CVBlock(
            title="SaaS Dev",
            content="General SaaS development",
            industry_tags=["general_saas"],
            metrics={"duration_years": 5},
        )
    ]
    s_dom_0, _ = calculate_domain_score(p0, b0, job)
    assert s_dom_0 == 0.0

    # 3 YoE: 0.50 + 0.10 * 3 = 0.80
    p3 = CandidatePersona(
        name="3 YoE HealthTech",
        years_experience=3,
        seniority_level="mid",
    )
    b3 = [
        CVBlock(
            title="Health Systems Dev",
            content="HIPAA claims processing",
            industry_tags=["healthtech"],
            metrics={"duration_years": 3},
        )
    ]
    s_dom_3, _ = calculate_domain_score(p3, b3, job)
    assert round(s_dom_3, 2) == 0.80

    # 5 YoE: 0.50 + 0.10 * 5 = 1.00
    p5 = CandidatePersona(
        name="5 YoE HealthTech",
        years_experience=5,
        seniority_level="senior",
    )
    b5 = [
        CVBlock(
            title="Health Systems Dev",
            content="HIPAA claims processing",
            industry_tags=["healthtech"],
            metrics={"duration_years": 5},
        )
    ]
    s_dom_5, _ = calculate_domain_score(p5, b5, job)
    assert round(s_dom_5, 2) == 1.00

    # 12 YoE: saturates at 1.00
    p12 = CandidatePersona(
        name="12 YoE HealthTech",
        years_experience=12,
        seniority_level="lead",
    )
    b12 = [
        CVBlock(
            title="Health Systems Lead",
            content="HIPAA claims processing",
            industry_tags=["healthtech"],
            metrics={"duration_years": 12},
        )
    ]
    s_dom_12, _ = calculate_domain_score(p12, b12, job)
    assert round(s_dom_12, 2) == 1.00


def test_healthtech_vs_gaming_domain_alignment_separation() -> None:
    """
    Dedicated benchmark test:
    Two 12-YoE candidates with identical senior backend stacks (Java/Python/AWS).
    - Candidate 1: 12 years deep HealthTech domain history (Optum, Epic, EDI, FHIR).
    - Candidate 2: 12 years Gaming/AdTech domain history (Riot Games, Trade Desk).

    Target Job: Optum Senior Backend Engineer (HealthTech strictness beta = 1.0).
    Verify that HealthTech candidate scores >= 12% (>= 0.12) higher in P(Match)
    than the Gaming candidate.
    Also verify parity on a domain-agnostic SaaS listing (beta = 0.0).
    """
    dataset_path = (
        Path(__file__).parent / "eval" / "datasets" / "healthtech_domain_benchmark.json"
    )
    assert dataset_path.exists(), f"Benchmark dataset missing at {dataset_path}"

    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)

    # 1. Build HealthTech Candidate
    ht_raw = data["candidates"]["healthtech_veteran"]
    ht_persona = CandidatePersona(
        name=ht_raw["name"],
        headline=ht_raw["headline"],
        years_experience=ht_raw["years_experience"],
        seniority_level=ht_raw["seniority_level"],
        target_roles=ht_raw["target_roles"],
    )
    ht_blocks = [
        CVBlock(
            title=b["title"],
            organization=b["organization"],
            content=b["content"],
            industry_tags=b["industry_tags"],
            metrics=b.get("metrics", {}),
            skills=b.get("skills", []),
        )
        for b in ht_raw["blocks"]
    ]
    ht_skills = set(ht_raw["skills"])

    # 2. Build Gaming Candidate
    gm_raw = data["candidates"]["gaming_veteran"]
    gm_persona = CandidatePersona(
        name=gm_raw["name"],
        headline=gm_raw["headline"],
        years_experience=gm_raw["years_experience"],
        seniority_level=gm_raw["seniority_level"],
        target_roles=gm_raw["target_roles"],
    )
    gm_blocks = [
        CVBlock(
            title=b["title"],
            organization=b["organization"],
            content=b["content"],
            industry_tags=b["industry_tags"],
            metrics=b.get("metrics", {}),
            skills=b.get("skills", []),
        )
        for b in gm_raw["blocks"]
    ]
    gm_skills = set(gm_raw["skills"])

    # 3. Build Jobs
    optum_raw = data["jobs"]["optum_healthtech_strict"]
    optum_job = JobListing(
        title=optum_raw["title"],
        company_name=optum_raw["company_name"],
        industry=optum_raw["industry"],
        industry_vertical=optum_raw["industry_vertical"],
        domain_strictness=optum_raw["domain_strictness"],
        raw_description=optum_raw["raw_description"],
        ats_requirements=optum_raw["ats_requirements"],
    )

    saas_raw = data["jobs"]["general_saas_agnostic"]
    saas_job = JobListing(
        title=saas_raw["title"],
        company_name=saas_raw["company_name"],
        industry=saas_raw["industry"],
        industry_vertical=saas_raw["industry_vertical"],
        domain_strictness=saas_raw["domain_strictness"],
        raw_description=saas_raw["raw_description"],
        ats_requirements=saas_raw["ats_requirements"],
    )

    # 4. Evaluate both on HealthTech Job
    ht_score, ht_breakdown = calculate_match_upgraded(
        persona=ht_persona,
        job=optum_job,
        blocks=ht_blocks,
        persona_skills=ht_skills,
    )

    gm_score, gm_breakdown = calculate_match_upgraded(
        persona=gm_persona,
        job=optum_job,
        blocks=gm_blocks,
        persona_skills=gm_skills,
    )

    # Verify Domain & Context score separation
    assert ht_breakdown.domain_score == 1.0, (
        f"Expected 1.0, got {ht_breakdown.domain_score}"
    )
    assert gm_breakdown.domain_score == 0.0, (
        f"Expected 0.0, got {gm_breakdown.domain_score}"
    )
    assert ht_breakdown.context_score == 1.0, (
        f"Expected 1.0, got {ht_breakdown.context_score}"
    )
    assert gm_breakdown.context_score == 0.0, (
        f"Expected 0.0, got {gm_breakdown.context_score}"
    )

    score_diff = ht_score - gm_score
    # Verify HealthTech candidate scores at least 12% (0.12) higher in overall P(Match)
    assert score_diff >= 0.12, (
        f"Expected score difference >= 0.12 (12%), got {score_diff:.4f} "
        f"(HealthTech: {ht_score}, Gaming: {gm_score})"
    )

    # 5. Evaluate both on Domain-Agnostic SaaS Job
    ht_saas_score, ht_saas_breakdown = calculate_match_upgraded(
        persona=ht_persona,
        job=saas_job,
        blocks=ht_blocks,
        persona_skills=ht_skills,
    )
    gm_saas_score, gm_saas_breakdown = calculate_match_upgraded(
        persona=gm_persona,
        job=saas_job,
        blocks=gm_blocks,
        persona_skills=gm_skills,
    )

    # On domain agnostic SaaS (beta = 0.0), context score falls back to archetype
    assert ht_saas_breakdown.context_score == ht_saas_breakdown.archetype_score
    assert gm_saas_breakdown.context_score == gm_saas_breakdown.archetype_score
    # Both candidates have identical stack; delta should be minimal (<= 0.02)
    assert abs(ht_saas_score - gm_saas_score) <= 0.02
