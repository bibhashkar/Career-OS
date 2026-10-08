"""
Unit tests for deterministic and hybrid requirements extraction, grounding validation,
and visa classification.
"""

from unittest.mock import MagicMock

import pytest

from app.ingestion.deterministic_extractor import (
    classify_visa_sponsorship,
    extract_deterministic_requirements,
    extract_years_of_experience,
)
from app.ingestion.extractor import HybridRequirementsExtractor
from app.ingestion.models import VisaSponsorshipStatus


def test_classify_visa_sponsorship_positive() -> None:
    assert (
        classify_visa_sponsorship(
            "We offer full relocation and visa sponsorship for this role."
        )
        == VisaSponsorshipStatus.YES
    )
    assert (
        classify_visa_sponsorship("Company will sponsor H-1B visas.")
        == VisaSponsorshipStatus.YES
    )


def test_classify_visa_sponsorship_negative() -> None:
    assert (
        classify_visa_sponsorship(
            "Candidate must be authorized to work without sponsorship."
        )
        == VisaSponsorshipStatus.NO
    )
    assert (
        classify_visa_sponsorship("We will not sponsor work visas at this time.")
        == VisaSponsorshipStatus.NO
    )


def test_classify_visa_sponsorship_unknown() -> None:
    assert (
        classify_visa_sponsorship(
            "We are looking for an energetic engineer to join our team."
        )
        == VisaSponsorshipStatus.UNKNOWN
    )


def test_extract_years_of_experience() -> None:
    assert (
        extract_years_of_experience("5+ years of software engineering experience.") == 5
    )
    assert (
        extract_years_of_experience("Minimum of 3 years building cloud services.") == 3
    )
    assert extract_years_of_experience("At least 7 years leading teams.") == 7
    assert extract_years_of_experience("No requirements stated.") is None


def test_extract_deterministic_requirements() -> None:
    desc = (
        "We are hiring a Senior Python Engineer. "
        "Must have 4+ years of experience with Python, FastAPI, and PostgreSQL. "
        "Experience with Docker and Kubernetes (k8s) is a plus. "
        "Visa sponsorship is available."
    )
    result = extract_deterministic_requirements(
        title="Senior Python Engineer",
        raw_description=desc,
    )

    assert "Python" in result.required_skills
    assert "FastAPI" in result.required_skills
    assert "PostgreSQL" in result.required_skills
    assert "Docker" in result.required_skills
    assert "Kubernetes" in result.required_skills
    assert result.min_experience_years == 4
    assert result.visa_sponsorship == VisaSponsorshipStatus.YES


@pytest.mark.asyncio
async def test_hybrid_extractor_grounding_validation() -> None:
    # Simulate LLM returning a hallucinated skill ("COBOL", "Rust")
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = (
        '{"required_skills": ["Python", "FastAPI", "COBOL", "Rust"], '
        '"preferred_skills": ["Docker", "Kubernetes"], '
        '"min_experience_years": 5, '
        '"visa_sponsorship": "yes"}'
    )

    async def async_ainvoke(*args: object, **kwargs: object) -> MagicMock:
        return mock_response

    mock_llm.ainvoke = async_ainvoke

    extractor = HybridRequirementsExtractor(llm=mock_llm)
    job_desc = (
        "We build high-performance microservices using Python and "
        "FastAPI with Docker on Kubernetes."
    )

    parsed = await extractor.extract_requirements(
        title="Backend Engineer",
        raw_description=job_desc,
        company_name="Acme Corp",
    )

    # Python and FastAPI are grounded
    assert "Python" in parsed.required_skills
    assert "FastAPI" in parsed.required_skills

    # Hallucinated skills must be stripped by Grounding Validation
    assert "COBOL" not in parsed.required_skills
    assert "Rust" not in parsed.required_skills

    # Grounded preferred skills
    assert "Docker" in parsed.preferred_skills
    assert "Kubernetes" in parsed.preferred_skills
