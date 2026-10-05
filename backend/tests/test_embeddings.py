"""Unit tests for embedding generation and CV ingestion pipeline."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.agents.tools.embeddings import (
    chunk_cv_text,
    embed_text,
    embed_texts,
    generate_deterministic_embedding,
    ingest_cv_blocks,
)
from app.main import app


def test_generate_deterministic_embedding_properties() -> None:
    """Verify deterministic embeddings are 1536-dim and unit-normalized."""
    vec1 = generate_deterministic_embedding("Python FastAPI Engineer", dim=1536)
    vec2 = generate_deterministic_embedding("Python FastAPI Engineer", dim=1536)
    vec3 = generate_deterministic_embedding("Rust Distributed Systems", dim=1536)

    assert len(vec1) == 1536
    assert vec1 == vec2
    assert vec1 != vec3

    norm = sum(x * x for x in vec1)
    assert pytest.approx(norm, rel=1e-3) == 1.0


@pytest.mark.asyncio
async def test_embed_text_and_texts() -> None:
    """Verify embed_text and embed_texts produce correct dimensional vectors."""
    v = await embed_text("FastAPI & PostgreSQL backend")
    assert len(v) == 1536

    batch = await embed_texts(["First block", "Second block"])
    assert len(batch) == 2
    assert len(batch[0]) == 1536
    assert len(batch[1]) == 1536


@pytest.mark.asyncio
async def test_chunk_cv_text() -> None:
    """Verify raw resume text is chunked into structured achievement blocks."""
    sample_cv = (
        "## Experience\n"
        "Staff AI Architect at Apex Labs. Led development of real-time "
        "LangGraph multi-agent routing engines and pgvector semantic search.\n\n"
        "## Projects\n"
        "Career-OS Open Source. Built decoupled FastAPI and React architecture "
        "with Docker deployment and Alembic migrations."
    )
    blocks = await chunk_cv_text(sample_cv)
    assert len(blocks) >= 2
    titles = [b["title"] for b in blocks]
    assert any("Staff AI" in t or "Experience" in t for t in titles)
    assert any("Career-OS" in t or "Projects" in t for t in titles)


@pytest.mark.asyncio
async def test_ingest_cv_blocks_pipeline() -> None:
    """Verify ingest_cv_blocks returns serialized blocks with embeddings."""
    user_id = uuid.uuid4()
    blocks = [
        {
            "category": "experience",
            "title": "Principal Architect",
            "organization": "CloudScale Inc",
            "content": "Engineered distributed streaming data systems.",
            "metrics": {"throughput": "100k events/sec"},
            "skills": ["Python", "FastAPI", "Docker"],
        }
    ]
    results = await ingest_cv_blocks(user_id=user_id, blocks=blocks)
    assert len(results) == 1
    assert results[0]["title"] == "Principal Architect"
    assert results[0]["has_embedding"] is True


def test_cv_ingest_api_endpoint() -> None:
    """Verify POST /api/cv/ingest endpoint decomposes resume and returns blocks."""
    client = TestClient(app)
    payload = {
        "raw_text": (
            "Senior Backend Engineer at NexusAI. Architected LangGraph workflows "
            "persisting state checkpoints to PostgreSQL. Improved API latency by 45%."
        )
    }
    response = client.post("/api/cv/ingest", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["blocks_ingested"] >= 1
    assert len(data["blocks"]) >= 1
    assert "user_id" in data
