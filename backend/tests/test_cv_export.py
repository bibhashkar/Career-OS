"""
Unit tests for CV export formatting and /api/cv/export endpoint.
"""

from fastapi.testclient import TestClient

from app.core.cv_export import format_cv_as_markdown, format_cv_as_plaintext
from app.main import app

client = TestClient(app)

SAMPLE_DRAFT = {
    "candidate_title": "Senior AI Systems Engineer",
    "target_company": "Anthropic",
    "professional_summary": (
        "Expert in stateful agent workflows, LangGraph, and PostgreSQL pgvector."
    ),
    "skills_highlighted": ["Python", "FastAPI", "LangGraph", "PostgreSQL"],
    "experience_blocks": [
        {
            "title": "Staff Backend Engineer",
            "organization": "Nexus Labs",
            "content": (
                "Engineered distributed agent runtime supporting 50k sessions."
            ),
            "metrics": {"latency_reduction": "45%", "throughput": "1000 rps"},
        }
    ],
}


def test_format_cv_as_markdown() -> None:
    """Verify markdown output contains title, summary, skills, and metrics."""
    md = format_cv_as_markdown(SAMPLE_DRAFT)
    assert "# Senior AI Systems Engineer" in md
    assert "**Target Company:** Anthropic" in md
    assert "## Core Competencies & Skills" in md
    assert "Python, FastAPI" in md
    assert "### Staff Backend Engineer - Nexus Labs" in md
    assert "Latency reduction: 45%" in md


def test_format_cv_as_plaintext() -> None:
    """Verify plaintext output is unformatted single-column text."""
    txt = format_cv_as_plaintext(SAMPLE_DRAFT)
    assert "SENIOR AI SYSTEMS ENGINEER" in txt
    assert "PROFESSIONAL SUMMARY" in txt
    assert "* Staff Backend Engineer (Nexus Labs)" in txt
    assert "latency_reduction: 45%" in txt


def test_export_endpoint_markdown() -> None:
    """Verify /api/cv/export returns markdown attachment."""
    resp = client.post(
        "/api/cv/export?export_format=markdown",
        json={"cv_draft": SAMPLE_DRAFT},
    )
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert (
        'attachment; filename="tailored_cv.md"' in resp.headers["content-disposition"]
    )
    assert "# Senior AI Systems Engineer" in resp.text


def test_export_endpoint_plaintext() -> None:
    """Verify /api/cv/export returns txt attachment."""
    resp = client.post(
        "/api/cv/export?export_format=txt",
        json={"cv_draft": SAMPLE_DRAFT},
    )
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert (
        'attachment; filename="tailored_cv.txt"' in resp.headers["content-disposition"]
    )
    assert "SENIOR AI SYSTEMS ENGINEER" in resp.text
