"""Unit tests for SQLAlchemy models structure, relationships, and naming."""

import uuid

from app.models import (
    Application,
    Base,
    CompanyDossier,
    CVBlock,
    FeedbackLog,
    JobListing,
    UserProfile,
)


def test_table_names_are_singular() -> None:
    """Verify all database table names strictly adhere to singular conventions."""
    expected_tables = {
        "user_profile",
        "job_listing",
        "company_dossier",
        "cv_block",
        "feedback_log",
        "application",
        "ats_board",
        "ingestion_run",
        "provider_usage",
        "provider_state",
        "ingestion_task",
    }
    actual_tables = {table.name for table in Base.metadata.tables.values()}
    assert expected_tables == actual_tables


def test_user_profile_instantiation() -> None:
    """Verify UserProfile model can be instantiated with default fields."""
    profile = UserProfile(
        full_name="Alice Developer",
        email="alice@example.com",
        visa_status="H-1B",
        remote_preference="Remote",
        tone_directives={"style": "concise", "confidence": "high"},
        target_roles=["Senior Backend Engineer", "AI Platform Engineer"],
        target_locations=["San Francisco, CA", "Remote"],
    )
    assert profile.full_name == "Alice Developer"
    assert profile.email == "alice@example.com"
    assert profile.visa_status == "H-1B"
    assert profile.tone_directives["style"] == "concise"


def test_job_listing_and_dossier_relationship() -> None:
    """Verify JobListing foreign key to CompanyDossier."""
    dossier_id = uuid.uuid4()
    dossier = CompanyDossier(
        id=dossier_id,
        company_name="TechCorp AI",
        domain="techcorp.ai",
        industry="Artificial Intelligence",
        tech_stack=["Python", "FastAPI", "LangGraph", "PostgreSQL"],
        recent_news=[{"title": "TechCorp Raises Series B", "year": 2026}],
        business_model="B2B SaaS subscription",
    )
    job = JobListing(
        title="Staff AI Engineer",
        company_name="TechCorp AI",
        url="https://techcorp.ai/jobs/123",
        raw_description="Build autonomous agents using LangGraph and pgvector.",
        ats_requirements={"skills": ["Python", "LangGraph", "pgvector"]},
        company_dossier_id=dossier_id,
    )
    assert job.company_name == dossier.company_name
    assert job.company_dossier_id == dossier.id


def test_cv_block_embedding_structure() -> None:
    """Verify CVBlock stores content, category, metrics, and vector embedding."""
    user_id = uuid.uuid4()
    dummy_embedding = [0.0] * 1536
    block = CVBlock(
        user_profile_id=user_id,
        category="experience",
        title="Lead Software Engineer at ScaleFlow",
        content="Designed distributed microservices handling 2M requests/min.",
        metrics={"throughput": "2M req/min", "latency": "15ms"},
        skills=["Python", "FastAPI", "PostgreSQL"],
        embedding=dummy_embedding,
    )
    assert block.category == "experience"
    assert block.user_profile_id == user_id
    assert len(block.embedding) == 1536


def test_feedback_log_instantiation() -> None:
    """Verify FeedbackLog stores thread_id, review feedback, and weights."""
    log = FeedbackLog(
        thread_id="thread_mock_123",
        user_feedback="Make interview responses more technical on system design.",
        prompt_weight_adjustments={"technical_depth": 0.85, "brevity": 0.9},
    )
    assert log.thread_id == "thread_mock_123"
    assert log.prompt_weight_adjustments["technical_depth"] == 0.85


def test_user_profile_cv_blocks_strict_restrict_cascade() -> None:
    """Verify user_profile.cv_blocks enforces strict RESTRICT without delete-orphan."""
    cascade_options = UserProfile.cv_blocks.property.cascade
    assert "delete-orphan" not in cascade_options
    assert "delete" not in cascade_options


def test_application_instantiation() -> None:
    """Verify Application model instantiation and default fields."""
    app_record = Application(
        user_profile_id=uuid.uuid4(),
        job_listing_id=uuid.uuid4(),
        status="saved",
    )
    assert app_record.status == "saved"
