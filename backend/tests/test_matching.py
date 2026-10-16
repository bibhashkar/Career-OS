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

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import create_access_token
from app.core.database import get_db
from app.main import app
from app.models.cv_block import CVBlock
from app.models.ingestion import ATSBoard, ATSProvider, IndustrySector
from app.models.job_listing import JobListing
from app.models.user_account import CandidatePersona, PersonaSkill, UserAccount
from app.services.matching import (
    calculate_achievement_score,
    calculate_freshness_score,
    calculate_prestige_score,
    calculate_probabilistic_gate,
    calculate_seniority_score,
    calculate_skill_overlap,
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
