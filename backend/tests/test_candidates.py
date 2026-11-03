"""
Unit tests for resume parser and candidate onboarding CRUD APIs.
"""

import io
import uuid
from collections.abc import AsyncGenerator

import docx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.core.database import get_db
from app.ingestion.resume_parser import (
    detect_is_linkedin_pdf,
    extract_candidate_name,
    extract_metrics,
    extract_skills_from_text,
    extract_text_from_docx,
    parse_linkedin_text,
    parse_resume_bytes,
)
from app.main import app
from app.models.user_account import UserAccount
from app.services.diagnostics import calculate_persona_completeness


def test_extract_skills_from_text() -> None:
    """Verify canonical technical skills normalization via SKILL_TAXONOMY."""
    sample_text = (
        "Built distributed event queues in Python using Kafka and PostgreSQL. "
        "Deployed on Kubernetes cluster with FastAPI and Docker."
    )
    skills = extract_skills_from_text(sample_text)
    assert "Python" in skills
    assert "Kafka" in skills
    assert "PostgreSQL" in skills
    assert "Kubernetes" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills


def test_extract_metrics() -> None:
    """Verify metric detection for latency, percentages, scale, and hackathons."""
    text = (
        "Awarded 1st place overall at ETHGlobal Hackathon. "
        "Reduced p99 query latency by 45% and cut costs by $250k. "
        "Scaled distributed engine to 2M req/s across 100,000+ active users."
    )
    metrics = extract_metrics(text)
    assert "percentage_impact" in metrics
    assert "financial_impact" in metrics
    assert "throughput_or_latency" in metrics
    assert "user_or_data_scale" in metrics
    assert "honor_placement" in metrics
    assert "1st place" in metrics["honor_placement"].lower()


def test_detect_and_parse_linkedin_text() -> None:
    """Verify LinkedIn 'Save to PDF' detection and structured parsing."""
    sample_linkedin = (
        "Contact\n"
        "jane.developer@example.com\n"
        "www.linkedin.com/in/jane-dev\n\n"
        "Top Skills\n"
        "Python\n"
        "FastAPI\n"
        "Apache Kafka\n\n"
        "Languages\n"
        "English\n\n"
        "Jane Developer\n"
        "Senior Backend & AI Infrastructure Engineer\n"
        "San Francisco Bay Area\n\n"
        "Summary\n"
        "Distributed systems engineer with 6 years experience in low-latency "
        "systems.\n\n"
        "Experience\n"
        "Senior Systems Engineer\n"
        "CloudScale Inc\n"
        "Designed asynchronous event-driven data pipeline using Kafka and Go. "
        "Decreased system latency by 40% and handled 1M daily requests.\n\n"
        "1st Place Winner - AI Track\n"
        "HackMIT\n"
        "Built decentralized model serving engine with vLLM and Redis in 48 hours."
    )
    assert detect_is_linkedin_pdf(sample_linkedin) is True
    parsed = parse_linkedin_text(sample_linkedin)

    assert parsed.full_name == "Jane Developer"
    assert parsed.email == "jane.developer@example.com"
    assert parsed.linkedin_url == "https://www.linkedin.com/in/jane-dev"
    assert len(parsed.blocks) >= 2

    # Check hackathon category detection
    hack_block = next(
        (b for b in parsed.blocks if b.category == "hackathon_achievement"), None
    )
    assert hack_block is not None
    assert hack_block.is_quantified is True


def test_extract_text_from_docx() -> None:
    """Verify Word DOCX text extraction."""
    doc = docx.Document()
    doc.add_heading("Alice Developer", level=1)
    doc.add_paragraph("Senior Python & Distributed Systems Engineer")
    doc.add_paragraph("Architected real-time streaming pipelines.")

    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_bytes = docx_buffer.getvalue()

    extracted = extract_text_from_docx(docx_bytes)
    assert "Alice Developer" in extracted
    assert "Senior Python" in extracted

    parsed = parse_resume_bytes(docx_bytes, "Alice_Resume.docx")
    assert parsed.full_name == "Alice Developer"
    assert "Python" in parsed.skills


@pytest.mark.asyncio
async def test_candidate_onboarding_and_persona_api_flow(
    db_session: AsyncSession,
) -> None:
    """Verify complete onboarding API flow, persona switcher, and block CRUD."""

    from sqlalchemy.ext.asyncio import async_sessionmaker

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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = create_access_token(
                user_id="11111111-2222-3333-4444-555555555555",
                email="cand100@example.com",
            )
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Parse text endpoint
            paste_payload = {
                "text": (
                    "Bob Engineer\n"
                    "bob@example.com | (555) 019-2831 | github.com/bobeng\n\n"
                    "# Experience\n"
                    "Senior Backend Engineer at DataCo\n"
                    "Architected high-throughput ingestion in Python & FastAPI "
                    "processing 50k req/s with 35% latency reduction.\n\n"
                    "# Hackathons & Honors\n"
                    "1st Place Winner at Global AI Hackathon\n"
                    "Built autonomous multi-agent task orchestrator using LangGraph."
                )
            }
            parse_resp = await client.post(
                "/api/candidates/parse-text", json=paste_payload
            )
            assert parse_resp.status_code == 200
            staged = parse_resp.json()
            assert staged["full_name"] == "Bob Engineer"
            assert staged["email"] == "bob@example.com"
            assert len(staged["blocks"]) >= 2

            # 2. Onboard candidate with verified blocks & specialized personas
            onboard_payload = {
                "full_name": "Bob Engineer",
                "visa_status": "H-1B",
                "citizenship_country_code": "US",
                "preferred_locations": ["San Francisco, CA", "Remote"],
                "remote_preference": "Remote",
                "target_roles": ["Senior Backend Engineer", "AI Platform Engineer"],
                "target_industries": ["ai_ml_infra", "hft_quant_trading"],
                "years_experience": 6,
                "seniority_level": "senior",
                "skills": ["Python", "FastAPI", "Kafka", "Docker", "PostgreSQL"],
                "blocks": staged["blocks"],
                "specialized_personas": [
                    {
                        "name": "AI Platform Engineer",
                        "headline": "Specializing in Large-Scale AI Orchestration",
                        "target_roles": ["AI Platform Engineer"],
                        "target_industries": ["ai_ml_infra"],
                        "seniority_level": "senior",
                        "years_experience": 4,
                        "skills": ["Python", "LangGraph", "FastAPI"],
                    }
                ],
            }
            onboard_resp = await client.post(
                "/api/candidates/onboard",
                headers=headers,
                json=onboard_payload,
            )
            assert onboard_resp.status_code == 200
            onboard_data = onboard_resp.json()
            assert onboard_data["status"] == "onboarded"
            assert onboard_data["blocks_ingested"] >= 2
            assert onboard_data["specialized_personas_created"] == 1

            # 3. List candidate personas
            personas_resp = await client.get(
                "/api/candidates/personas", headers=headers
            )
            assert personas_resp.status_code == 200
            personas_list = personas_resp.json()
            # Must contain at least Universal Persona + Specialized Persona
            assert len(personas_list) >= 2
            universal = next((p for p in personas_list if p["is_common_persona"]), None)
            specialized = next(
                (p for p in personas_list if not p["is_common_persona"]), None
            )
            assert universal is not None
            assert specialized is not None
            assert universal["is_default"] is True
            assert specialized["name"] == "AI Platform Engineer"

            # 4. Set specialized persona as active default
            set_def_resp = await client.put(
                f"/api/candidates/personas/{specialized['id']}/default",
                headers=headers,
            )
            assert set_def_resp.status_code == 200

            # 5. List CV blocks
            blocks_resp = await client.get("/api/candidates/blocks", headers=headers)
            assert blocks_resp.status_code == 200
            blocks_list = blocks_resp.json()
            assert len(blocks_list) >= 2
            assert any(b["has_embedding"] for b in blocks_list)

            # 6. Add new hackathon achievement block
            new_block_payload = {
                "category": "hackathon_achievement",
                "title": "1st Place Winner - AI Infra Track",
                "organization": "ETHGlobal",
                "content": (
                    "Built open-source decentralized LLM scheduler in Go & Kafka."
                ),
                "metrics": {"placement": "1st Place", "github_stars": 350},
                "skills": ["Go", "Kafka", "Distributed Systems"],
            }
            add_block_resp = await client.post(
                "/api/candidates/blocks",
                headers=headers,
                json=new_block_payload,
            )
            assert add_block_resp.status_code == 201
            new_block_id = add_block_resp.json()["id"]

            # 7. Delete block
            del_resp = await client.delete(
                f"/api/candidates/blocks/{new_block_id}",
                headers=headers,
            )
            assert del_resp.status_code == 200
            assert del_resp.json()["status"] == "deleted"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_persona_management_and_uniqueness_flow(
    db_session: AsyncSession,
) -> None:
    """
    Verify persona editing, renaming, case-insensitive duplicate guards,
    and Universal Profile rename/delete protections.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            user_id = "22222222-3333-4444-5555-666666666666"
            token = create_access_token(
                user_id=user_id,
                email="persona_mgr@example.com",
            )
            headers = {"Authorization": f"Bearer {token}"}

            # 1. Onboard candidate to create root account and Universal Profile
            onboard_payload = {
                "full_name": "Persona Manager Test",
                "visa_status": "Citizen",
                "target_roles": ["Software Engineer"],
                "years_experience": 5,
                "skills": ["Python", "FastAPI"],
            }
            onb_res = await client.post(
                "/api/candidates/onboard",
                headers=headers,
                json=onboard_payload,
            )
            assert onb_res.status_code == 200

            # 2. Retrieve personas (initially contains Universal Profile)
            list_res = await client.get("/api/candidates/personas", headers=headers)
            assert list_res.status_code == 200
            personas = list_res.json()
            assert len(personas) == 1
            universal_p = personas[0]
            assert universal_p["is_common_persona"] is True
            assert universal_p["name"] == "Universal Profile"

            # 3. Create a specialized persona "AI Engineer"
            create_payload = {
                "name": "AI Engineer",
                "headline": "LLM Infrastructure Specialist",
                "target_roles": ["AI Engineer"],
                "seniority_level": "senior",
                "years_experience": 4,
                "skills": ["PyTorch", "vLLM"],
            }
            create_res = await client.post(
                "/api/candidates/personas",
                headers=headers,
                json=create_payload,
            )
            assert create_res.status_code == 201
            ai_persona = create_res.json()
            assert ai_persona["name"] == "AI Engineer"

            # 4. Attempt to create duplicate name (case-insensitive "ai engineer")
            dup_create_res = await client.post(
                "/api/candidates/personas",
                headers=headers,
                json={"name": "ai engineer", "skills": ["Python"]},
            )
            assert dup_create_res.status_code == 400
            assert "already exists" in dup_create_res.json()["detail"]

            # 5. Create a second specialized persona "Backend Specialist"
            create_res2 = await client.post(
                "/api/candidates/personas",
                headers=headers,
                json={"name": "Backend Specialist", "skills": ["Go", "Kafka"]},
            )
            assert create_res2.status_code == 201
            backend_persona = create_res2.json()

            # 6. Rename "Backend Specialist" to "Distributed Systems Architect"
            update_payload = {
                "name": "Distributed Systems Architect",
                "headline": "High-Throughput Systems",
                "target_roles": ["Principal Architect"],
                "seniority_level": "principal",
                "years_experience": 10,
                "skills": ["Go", "Kafka", "Rust"],
            }
            update_res = await client.put(
                f"/api/candidates/personas/{backend_persona['id']}",
                headers=headers,
                json=update_payload,
            )
            assert update_res.status_code == 200
            updated_p = update_res.json()
            assert updated_p["name"] == "Distributed Systems Architect"
            assert updated_p["years_experience"] == 10

            # 7. Attempt to rename to "ai engineer" (conflict with Persona 1)
            conflict_update_res = await client.put(
                f"/api/candidates/personas/{backend_persona['id']}",
                headers=headers,
                json={
                    "name": "ai engineer",
                    "headline": "Conflicting",
                    "target_roles": [],
                },
            )
            assert conflict_update_res.status_code == 400
            assert "already exists" in conflict_update_res.json()["detail"]

            # 8. Attempt to rename the Universal Profile (must be rejected)
            universal_rename_res = await client.put(
                f"/api/candidates/personas/{universal_p['id']}",
                headers=headers,
                json={
                    "name": "Custom Profile Name",
                    "headline": "Changed headline",
                    "target_roles": ["CTO"],
                },
            )
            assert universal_rename_res.status_code == 400
            assert "cannot be renamed" in universal_rename_res.json()["detail"]

            # 9. Modifying settings of Universal Profile with same name succeeds
            universal_update_res = await client.put(
                f"/api/candidates/personas/{universal_p['id']}",
                headers=headers,
                json={
                    "name": "Universal Profile",
                    "headline": "Updated Universal Headline",
                    "target_roles": ["Director of Engineering"],
                    "seniority_level": "lead",
                    "years_experience": 8,
                    "skills": ["Python", "FastAPI", "PostgreSQL"],
                },
            )
            assert universal_update_res.status_code == 200
            upd_univ = universal_update_res.json()
            assert upd_univ["headline"] == "Updated Universal Headline"
            assert upd_univ["seniority_level"] == "lead"

            # 10. Attempt to delete Universal Profile (must be rejected)
            del_univ_res = await client.delete(
                f"/api/candidates/personas/{universal_p['id']}",
                headers=headers,
            )
            assert del_univ_res.status_code == 400
            assert "cannot be deleted" in del_univ_res.json()["detail"]

            # 11. Set specialized persona as default, then delete it
            await client.put(
                f"/api/candidates/personas/{ai_persona['id']}/default",
                headers=headers,
            )
            del_ai_res = await client.delete(
                f"/api/candidates/personas/{ai_persona['id']}",
                headers=headers,
            )
            assert del_ai_res.status_code == 200
            assert del_ai_res.json()["status"] == "deleted"

            # 12. Verify Universal Profile is automatically restored as default
            list_res2 = await client.get("/api/candidates/personas", headers=headers)
            personas2 = list_res2.json()
            univ_after = next(p for p in personas2 if p["is_common_persona"])
            assert univ_after["is_default"] is True

            # 13. Test CVBlock update endpoint (PUT /api/candidates/blocks/{id})
            create_block_res = await client.post(
                "/api/candidates/blocks",
                json={
                    "category": "experience",
                    "title": "Senior Systems Engineer",
                    "organization": "CloudScale",
                    "content": "Architected low-latency distributed pipeline.",
                    "metrics": {"percentage": "40%"},
                    "skills": ["Python", "FastAPI"],
                },
                headers=headers,
            )
            assert create_block_res.status_code == 201
            block_data = create_block_res.json()
            block_id = block_data["id"]

            update_block_res = await client.put(
                f"/api/candidates/blocks/{block_id}",
                json={
                    "title": "Staff Distributed Systems Architect",
                    "content": "Architected high-throughput payment ledgers scaling to 10k ops/sec with PostgreSQL.",
                    "metrics": {"throughput": "10k ops/sec"},
                    "skills": ["Python", "PostgreSQL", "FastAPI"],
                },
                headers=headers,
            )
            assert update_block_res.status_code == 200
            updated = update_block_res.json()
            assert updated["title"] == "Staff Distributed Systems Architect"
            assert "10k ops/sec" in updated["content"]
            assert updated["metrics"]["throughput"] == "10k ops/sec"
            assert "PostgreSQL" in updated["skills"]
            assert updated["has_embedding"] is True

            # 14. Verify CVBlock deduplication: post identical block with same content & organization
            dup_block_res = await client.post(
                "/api/candidates/blocks",
                json={
                    "category": "experience",
                    "title": "Senior Systems Engineer Duplicate",
                    "organization": "CloudScale",
                    "content": "Architected high-throughput payment ledgers scaling to 10k ops/sec with PostgreSQL.",
                    "metrics": {"percentage": "40%"},
                    "skills": ["Python", "FastAPI"],
                },
                headers=headers,
            )
            assert dup_block_res.status_code == 200
            dup_data = dup_block_res.json()
            assert dup_data["id"] == block_id

            # 15. Verify update_persona with contact PII
            update_persona_res = await client.put(
                f"/api/candidates/personas/{univ_after['id']}",
                json={
                    "name": "Universal Profile",
                    "full_name": "Bob Updated Engineer",
                    "email": "bob.updated@example.com",
                    "phone": "+1 555-999-8888",
                    "headline": "Staff Systems Architect",
                    "seniority_level": "staff",
                    "years_experience": 10,
                },
                headers=headers,
            )
            assert update_persona_res.status_code == 200
            up_data = update_persona_res.json()
            assert up_data["full_name"] == "Bob Updated Engineer"
            assert up_data["email"] == "bob.updated@example.com"
            assert up_data["phone"] == "+1 555-999-8888"
            assert (
                up_data["career_intelligence"]["contact_pii"]["phone"]
                == "+1 555-999-8888"
            )

            # 16. Verify GET /api/candidates/personas returns the persisted contact PII
            get_personas_res = await client.get(
                "/api/candidates/personas", headers=headers
            )
            assert get_personas_res.status_code == 200
            p_list = get_personas_res.json()
            univ_p = next(p for p in p_list if p["id"] == univ_after["id"])
            assert univ_p["full_name"] == "Bob Updated Engineer"
            assert univ_p["email"] == "bob.updated@example.com"
            assert univ_p["phone"] == "+1 555-999-8888"
            assert (
                univ_p["career_intelligence"]["contact_pii"]["email"]
                == "bob.updated@example.com"
            )

            # 17. Verify update_persona with career_intelligence payload and duplicate email resilience
            update_with_ci_res = await client.put(
                f"/api/candidates/personas/{univ_after['id']}",
                json={
                    "name": "Universal Profile",
                    "full_name": "Bob Senior Lead",
                    "email": "lead.candidate@example.com",
                    "phone": "+1 555-000-1111",
                    "headline": "Lead Systems Architect",
                    "seniority_level": "lead",
                    "years_experience": 12,
                    "career_intelligence": {
                        "education": [],
                        "work_experience": [],
                    },
                },
                headers=headers,
            )
            assert update_with_ci_res.status_code == 200
            ci_data = update_with_ci_res.json()
            assert ci_data["full_name"] == "Bob Senior Lead"
            assert ci_data["email"] == "lead.candidate@example.com"
            assert ci_data["phone"] == "+1 555-000-1111"
            assert (
                ci_data["career_intelligence"]["contact_pii"]["full_name"]
                == "Bob Senior Lead"
            )
            assert (
                ci_data["career_intelligence"]["contact_pii"]["email"]
                == "lead.candidate@example.com"
            )
            assert (
                ci_data["career_intelligence"]["contact_pii"]["phone"]
                == "+1 555-000-1111"
            )

            # 18. Verify duplicate email on another account does not trigger 500 UniqueViolation
            other_uid = uuid.uuid4()
            other_acc = UserAccount(
                id=other_uid,
                email="registered.conflict@example.com",
                full_name="Other User",
                role="candidate",
            )
            db_session.add(other_acc)
            await db_session.commit()

            conflict_email_res = await client.put(
                f"/api/candidates/personas/{univ_after['id']}",
                json={
                    "name": "Universal Profile",
                    "full_name": "Bob Conflict Test",
                    "email": "registered.conflict@example.com",
                    "phone": "+1 555-222-3333",
                    "headline": "Lead Systems Architect",
                    "seniority_level": "lead",
                    "years_experience": 12,
                },
                headers=headers,
            )
            assert conflict_email_res.status_code == 200
            conf_data = conflict_email_res.json()
            assert conf_data["full_name"] == "Bob Conflict Test"
            assert conf_data["email"] == "registered.conflict@example.com"
            assert conf_data["phone"] == "+1 555-222-3333"
            assert (
                conf_data["career_intelligence"]["contact_pii"]["email"]
                == "registered.conflict@example.com"
            )
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_calculate_persona_completeness_capability_gating() -> None:
    """
    Verify deterministic candidate capability gating:
    If candidate sets roles/visa/seniority but zero capability signals (skills, CV blocks,
    education, projects, role tenures), completeness must strictly evaluate to 0% and
    is_profile_ready must be False with honest cold-start status reason.
    """
    # 1. Zero capability signals (Admin seed profile / fresh empty user)
    cold_result = calculate_persona_completeness(
        target_roles=["Administrator"],
        years_experience=10,
        seniority_level="staff",
        skills=[],
        blocks=[],
        career_intelligence={},
        visa_status="Citizen",
        preferred_locations=["Remote"],
    )
    assert cold_result.score == 0
    assert cold_result.is_profile_ready is False
    assert "haven't shared your skills or profile" in cold_result.status_reason
    assert cold_result.pillars.role_trajectory == 0
    assert cold_result.pillars.skills_inventory == 0

    # 2. Candidate adds capability signal (1 skill + roles)
    active_result = calculate_persona_completeness(
        target_roles=["Administrator"],
        years_experience=10,
        seniority_level="staff",
        skills=["Kubernetes"],
        blocks=[],
        career_intelligence={},
        visa_status="Citizen",
        preferred_locations=["Remote"],
    )
    # role (8+4=12) + skills (4) + logistics (3+3=6) = 22%
    assert active_result.score >= 10
    assert active_result.is_profile_ready is True
    assert "Grounded matching is active" in active_result.status_reason


def test_extract_candidate_name_edge_cases() -> None:
    """Verify name extraction with explicit anchors, punctuation, and email fallbacks."""
    # Explicit anchor
    t1 = "Curriculum Vitae of Alice M. Walker\nSenior Engineer"
    lines1 = [line_item.strip() for line_item in t1.split("\n") if line_item.strip()]
    assert extract_candidate_name(t1, lines1) == "Alice M. Walker"

    # Name with pronouns
    t2 = "David Zhang (he/him)\nFull Stack Developer"
    lines2 = [line_item.strip() for line_item in t2.split("\n") if line_item.strip()]
    assert extract_candidate_name(t2, lines2) == "David Zhang"

    # Email username fallback
    t3 = "Software Engineer\nSummary of qualifications\njohn.doe@example.com"
    lines3 = [line_item.strip() for line_item in t3.split("\n") if line_item.strip()]
    assert (
        extract_candidate_name(t3, lines3, emails=["john.doe@example.com"])
        == "John Doe"
    )


def test_multi_disciplinary_metrics_and_projects() -> None:
    """Verify regex improvements for business, leadership, scale, and project extraction."""
    from app.ingestion.resume_parser import (
        _extract_deterministic_projects,
        extract_quantified_metrics,
    )
    from app.schemas.candidate_dossier import (
        normalize_award_record,
        normalize_institution_tier,
    )
    from app.services.matching import calculate_prestige_score

    # 1. Metric extraction tests
    b1 = "Optimized transaction file generation by 42%, reducing request processing to <2 seconds for 1,000+ concurrent dataset"
    m1 = extract_quantified_metrics(b1)
    types1 = {m.metric_type for m in m1}
    assert "percentage_improvement" in types1
    assert "latency_optimization" in types1
    assert "scale_users_or_data" in types1

    b2 = "Mentored 8+ developers on system architecture and code review"
    m2 = extract_quantified_metrics(b2)
    assert any(m.metric_type == "team_leadership" for m in m2)

    b3 = "Managing 10,000+ daily requests with high-concurrency tracking"
    m3 = extract_quantified_metrics(b3)
    assert any(m.metric_type == "scale_users_or_data" for m in m3)

    b4 = "Architected EDI system handling $7B+ in annual volume"
    m4 = extract_quantified_metrics(b4)
    assert any(m.metric_type == "financial_volume" for m in m4)

    # 2. Project extraction
    proj_lines = [
        "Distributed Ledger: Built low-latency payment engine in Rust processing 10k ops/sec. https://github.com/example/ledger",
        "AI Workflow Automation | Architected multi-agent graph with LangGraph cutting manual review time by 65%.",
    ]
    projects, blocks = _extract_deterministic_projects(proj_lines)
    assert len(projects) == 2
    assert projects[0].name == "Distributed Ledger"
    assert projects[0].repository_url == "https://github.com/example/ledger"
    assert len(blocks) == 2
    assert blocks[0].category == "project"

    # 3. Normalization helpers
    assert normalize_institution_tier("tier_1") == "tier_1_ivy_top_tech"
    assert normalize_institution_tier("tier_2") == "tier_2_state_flagship"
    assert normalize_institution_tier("standard") == "standard"

    raw_aw = {"title": "1st Place Winner", "description": "MIT Hackathon"}
    norm_aw = normalize_award_record(raw_aw)
    assert norm_aw["title"] == "1st Place Winner"
    assert norm_aw["event_or_issuer"] == "MIT Hackathon"

    # 4. Prestige score with education records
    score_tier1 = calculate_prestige_score(
        [], education_records=[{"institution_tier": "tier_1_ivy_top_tech"}]
    )
    assert score_tier1 == 1.0

    score_tier2 = calculate_prestige_score(
        [], education_records=[{"institution_tier": "tier_2_state_flagship"}]
    )
    assert score_tier2 == 0.8
