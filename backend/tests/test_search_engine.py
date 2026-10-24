"""
Comprehensive test suite for the Command-Facet Search Engine,
Tokenized Omnibar parser, and Discovery Architecture (Spec v1.0.0).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.core.database import get_db
from app.main import app
from app.models.ingestion import ATSBoard, ATSProvider, IndustrySector
from app.models.job_listing import JobListing
from app.models.user_account import CandidatePersona, UserAccount
from app.schemas.search import (
    JobSearchFilterDTO,
    SearchMode,
    WorkAuthTier,
    WorkplaceModality,
)
from app.services.matching import (
    build_stage1_query,
    diagnose_zero_results,
    haversine_miles,
    retrieve_and_rank_jobs,
)
from app.services.search_parser import OmnisearchParser


def test_omnisearch_tokenizer_extraction() -> None:
    """Test fast in-memory tri-word, two-word, and single-word token extraction."""
    # 1. Multi-entity string
    raw_query = "Stripe Lead HealthTech Backend Engineer Remote Kubernetes"
    extracted = OmnisearchParser.parse_query(raw_query)

    assert "stripe" in extracted.companies
    assert "lead" in extracted.seniority_levels
    assert "healthtech" in extracted.target_industries
    assert extracted.workplace_modality == "remote"
    assert "kubernetes" in extracted.must_have_skills
    # Residual text should have remaining non-entity words
    assert "backend" in extracted.residual_query.lower()
    assert "engineer" in extracted.residual_query.lower()

    # 2. Multi-word company and industry
    raw_query_2 = "Epic Systems healthcare_it distributed transactions"
    extracted_2 = OmnisearchParser.parse_query(raw_query_2)
    assert "epic systems" in extracted_2.companies
    assert "healthtech" in extracted_2.target_industries
    assert "distributed transactions" in extracted_2.residual_query

    # 3. Empty query returns default DTO
    empty_res = OmnisearchParser.parse_query("   ")
    assert empty_res.companies == []
    assert empty_res.residual_query == ""


def test_haversine_distance_calculation() -> None:
    """Verify geodesic distance calculation between geographic coordinates."""
    # San Francisco (37.7749, -122.4194) to Oakland (37.8044, -122.2712) ~ 8.4 miles
    sf_lat, sf_lng = 37.7749, -122.4194
    oak_lat, oak_lng = 37.8044, -122.2712
    distance = haversine_miles(sf_lat, sf_lng, oak_lat, oak_lng)
    assert 7.5 < distance < 9.5

    # Same location yields 0.0 miles
    assert haversine_miles(sf_lat, sf_lng, sf_lat, sf_lng) == 0.0


def test_stage1_query_strict_null_safety() -> None:
    """Verify that unselected filters generate zero restrictive WHERE clauses."""
    empty_filters = JobSearchFilterDTO(
        search_mode=SearchMode.UNBIASED,
        work_auth_tier=WorkAuthTier.ALL,
        workplace_modality=WorkplaceModality.ALL,
        min_base_salary_usd=None,
        candidate_geo=None,
        max_commute_miles=None,
        companies=[],
        target_industries=[],
        seniority_levels=[],
        must_have_skills=[],
        raw_query=None,
    )

    query = build_stage1_query(empty_filters)
    where_str = str(query.whereclause)

    # Must contain base active check
    assert "job_listing.status = :status_1" in where_str
    # Must NOT contain work auth, salary, or commute constraints
    assert "visa_sponsorship" not in where_str
    assert "salary_min_usd" not in where_str
    assert "is_everify_confirmed" not in where_str
    assert "workplace_type" not in where_str


@pytest.mark.asyncio
async def test_tri_tier_work_auth_and_diagnostics(
    db_session: AsyncSession,
) -> None:
    """
    Test tri-tier work auth filtering and zero-dead-end constraint diagnostics.
    """
    board_uuid = uuid.uuid4()
    provider = ATSProvider(
        code="greenhouse_test",
        name="Greenhouse Test",
        api_base_url="https://test.greenhouse.io",
        auth_type="public_api",
        is_active=True,
    )
    board = ATSBoard(
        id=board_uuid,
        provider="greenhouse_test",
        slug="testcorp",
        company_name="TestCorp",
        tier=1,
        priority=10,
        is_active=True,
    )
    industry = IndustrySector(
        code="healthtech_search",
        name="HealthTech",
        description="Health Systems",
        is_active=True,
    )
    db_session.add_all([provider, board, industry])
    await db_session.flush()

    # Job 1: F-1 OPT friendly (E-Verify confirmed, no citizenship restriction)
    job_f1 = JobListing(
        id=uuid.uuid4(),
        title="Software Engineer - Systems",
        company_name="TestCorp",
        ats_board_id=board_uuid,
        ats_provider="greenhouse_test",
        ats_board_slug="testcorp",
        source_job_id="f1-1",
        industry="healthtech_search",
        workplace_type="remote",
        salary_range="$150,000",
        salary_min_usd=150000,
        salary_max_usd=170000,
        raw_description="Distributed backend in Python",
        is_everify_confirmed=True,
        citizenship_restricted=False,
        visa_sponsorship="unknown",
        status="active",
        posted_at=datetime.now(UTC),
    )

    # Job 2: US Citizens Only (Defense/Gov restricted)
    job_citizen_only = JobListing(
        id=uuid.uuid4(),
        title="Security Infrastructure Engineer",
        company_name="TestCorp",
        ats_board_id=board_uuid,
        ats_provider="greenhouse_test",
        ats_board_slug="testcorp",
        source_job_id="cit-2",
        industry="healthtech_search",
        workplace_type="on_site",
        salary_range="$220,000",
        salary_min_usd=220000,
        raw_description="Requires US Citizenship and Top Secret clearance",
        is_everify_confirmed=True,
        citizenship_restricted=True,
        visa_sponsorship="no",
        status="active",
        posted_at=datetime.now(UTC),
    )

    # Job 3: H-1B Sponsoring Scaleup (>= 5 filings)
    job_h1b = JobListing(
        id=uuid.uuid4(),
        title="Staff Data Engineer",
        company_name="TestCorp",
        ats_board_id=board_uuid,
        ats_provider="greenhouse_test",
        ats_board_slug="testcorp",
        source_job_id="h1b-3",
        industry="healthtech_search",
        workplace_type="hybrid",
        salary_range="$200,000",
        salary_min_usd=200000,
        raw_description="Data pipelines in Python and SQL.",
        uscis_filings_count=28,
        visa_sponsorship="yes",
        citizenship_restricted=False,
        status="active",
        posted_at=datetime.now(UTC),
    )

    db_session.add_all([job_f1, job_citizen_only, job_h1b])
    await db_session.commit()

    # 1. Test F-1 OPT Filter
    f1_filters = JobSearchFilterDTO(
        search_mode=SearchMode.UNBIASED,
        work_auth_tier=WorkAuthTier.F1_OPT_CPT,
    )
    f1_query = build_stage1_query(f1_filters)
    f1_results = (await db_session.execute(f1_query)).scalars().all()
    f1_ids = {j.id for j in f1_results}

    assert job_f1.id in f1_ids
    assert job_citizen_only.id not in f1_ids

    # 2. Test H-1B Transfer Sponsorship Filter
    h1b_filters = JobSearchFilterDTO(
        search_mode=SearchMode.UNBIASED,
        work_auth_tier=WorkAuthTier.H1B_TRANSFER_SPONSOR,
    )
    h1b_query = build_stage1_query(h1b_filters)
    h1b_results = (await db_session.execute(h1b_query)).scalars().all()
    h1b_ids = {j.id for j in h1b_results}

    assert job_h1b.id in h1b_ids
    assert job_citizen_only.id not in h1b_ids

    # 3. Test Zero-Dead-End Diagnostic Relaxer
    # Combine contradictory filters: salary floor $300k (which none meet)
    impossible_filters = JobSearchFilterDTO(
        search_mode=SearchMode.UNBIASED,
        work_auth_tier=WorkAuthTier.H1B_TRANSFER_SPONSOR,
        min_base_salary_usd=300000,
    )
    diag = await diagnose_zero_results(db_session, impossible_filters)
    assert diag.status == "zero_results"
    assert diag.primary_bottleneck is not None
    assert diag.primary_bottleneck.restrictive_facet == "min_base_salary_usd"
    assert diag.primary_bottleneck.relaxed_patch == {"min_base_salary_usd": None}


@pytest.mark.asyncio
async def test_unbiased_market_explorer_mode(
    db_session: AsyncSession,
) -> None:
    """
    Verify that Market Explorer mode (UNBIASED) decouples candidate persona,
    returning raw listings ordered objectively by user criteria.
    """
    user_uuid = uuid.uuid4()
    account = UserAccount(
        id=user_uuid,
        email="unbiased.test@example.com",
        full_name="Explorer",
        visa_status="None",
        is_active=True,
    )
    persona = CandidatePersona(
        id=uuid.uuid4(),
        user_account_id=user_uuid,
        name="Explorer Profile",
        target_roles=["Frontend Engineer"],
        years_experience=1,
        seniority_level="entry",
    )
    board_uuid = uuid.uuid4()
    provider = ATSProvider(
        code="greenhouse_unbiased",
        name="Greenhouse Unbiased",
        api_base_url="https://test.greenhouse.io",
        auth_type="public_api",
        is_active=True,
    )
    board = ATSBoard(
        id=board_uuid,
        provider="greenhouse_unbiased",
        slug="alphacorp",
        company_name="Alpha Corp",
        tier=1,
        priority=10,
        is_active=True,
    )
    db_session.add_all([account, persona, provider, board])
    await db_session.flush()

    # Job A: Lower salary, posted today
    job_a = JobListing(
        id=uuid.uuid4(),
        title="Lead Platform Architect",
        company_name="Alpha Corp",
        ats_board_id=board_uuid,
        ats_provider="greenhouse_unbiased",
        ats_board_slug="alphacorp",
        source_job_id="alpha-1",
        industry="technology_software",
        workplace_type="remote",
        salary_min_usd=160000,
        salary_max_usd=190000,
        raw_description="Lead platform architecture and cloud infrastructure.",
        status="active",
        posted_at=datetime.now(UTC),
    )
    # Job B: Higher salary, posted 5 days ago
    job_b = JobListing(
        id=uuid.uuid4(),
        title="Staff ML Engineer",
        company_name="Beta Corp",
        ats_board_id=board_uuid,
        ats_provider="greenhouse_unbiased",
        ats_board_slug="alphacorp",
        source_job_id="beta-2",
        industry="technology_software",
        workplace_type="remote",
        salary_min_usd=230000,
        salary_max_usd=260000,
        raw_description="Staff Machine Learning infrastructure.",
        status="active",
        posted_at=datetime.now(UTC) - timedelta(days=5),
    )
    db_session.add_all([job_a, job_b])
    await db_session.commit()

    # Test sorting by salary in UNBIASED mode
    unbiased_salary_filters = JobSearchFilterDTO(
        search_mode=SearchMode.UNBIASED,
        sort_by="salary",
    )
    results, total_cnt = await retrieve_and_rank_jobs(
        db=db_session,
        persona=persona,
        account=account,
        blocks=[],
        filters=unbiased_salary_filters,
    )

    assert total_cnt >= 2
    # First job should be job_b because it has higher salary ($260k vs $190k)
    assert results[0].job_id == str(job_b.id)
    assert results[0].breakdown is None
    assert "Market Explorer Mode" in results[0].gate_notes[0]


@pytest.mark.asyncio
async def test_parse_query_api_endpoint(db_session: AsyncSession) -> None:
    """Test POST /api/jobs/parse-query returns tokenized entities."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = create_access_token(
            user_id=str(uuid.uuid4()),
            email="parse.test@example.com",
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/jobs/parse-query",
            json={"raw_text": "Stripe Senior HealthTech Backend Engineer Remote $180k"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "stripe" in data["companies"]
        assert "senior" in data["seniority_levels"]
        assert "healthtech" in data["target_industries"]
        assert data["workplace_modality"] == "remote"
        assert "backend engineer" in data["residual_query"].lower()
