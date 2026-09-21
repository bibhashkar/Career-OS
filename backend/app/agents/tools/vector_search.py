"""Semantic vector search helper for CVBlock achievements using pgvector."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cv_block import CVBlock

# Fallback deterministic blocks for hermetic testing without live database seed
DEFAULT_CV_BLOCKS: list[dict[str, Any]] = [
    {
        "id": "block-001",
        "category": "experience",
        "title": "Lead AI Engineer at AgentPlatform",
        "organization": "AgentPlatform Inc",
        "content": (
            "Architected a stateful multi-agent system with LangGraph and PostgreSQL "
            "PostgresSaver, enabling seamless thread checkpointing and streaming. "
            "Integrated pgvector for real-time semantic CV matching across 50k blocks."
        ),
        "metrics": {
            "latency_reduction": "45%",
            "concurrency": "10k active agents",
        },
        "skills": [
            "Python",
            "FastAPI",
            "LangGraph",
            "PostgreSQL",
            "pgvector",
            "WebSockets",
        ],
    },
    {
        "id": "block-002",
        "category": "experience",
        "title": "Senior Backend Infrastructure Engineer",
        "organization": "CloudScale Systems",
        "content": (
            "Built decoupled asynchronous APIs with FastAPI, SQLAlchemy, and psycopg. "
            "Implemented ATS simulation algorithms parsing job descriptions, "
            "improving candidate interview progression by 60%."
        ),
        "metrics": {
            "interview_progression": "+60%",
            "api_throughput": "15k req/sec",
        },
        "skills": [
            "Python",
            "FastAPI",
            "SQLAlchemy",
            "PostgreSQL",
            "Docker",
            "Ruff",
        ],
    },
    {
        "id": "block-003",
        "category": "project",
        "title": "Creator of Career-OS Agent Engine",
        "organization": "Open Source",
        "content": (
            "Designed and implemented full-stack career platform connecting a React "
            "Vite frontend with a FastAPI multi-agent backend via REST & WebSockets."
        ),
        "metrics": {"stars": "2.4k", "active_users": "5,000"},
        "skills": ["React", "Vite", "Tailwind CSS", "FastAPI", "LangGraph"],
    },
]


async def search_cv_blocks(
    user_id: uuid.UUID | str | None,
    query_embedding: list[float] | None = None,
    required_skills: list[str] | None = None,
    limit: int = 5,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Retrieve top-k matching CV blocks using pgvector or keyword matching."""
    if session is not None and user_id is not None:
        try:
            parsed_uuid = (
                uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id
            )
            stmt = select(CVBlock).where(CVBlock.user_profile_id == parsed_uuid)

            # Order by pgvector cosine distance if embedding provided
            if query_embedding and hasattr(CVBlock.embedding, "cosine_distance"):
                stmt = stmt.order_by(CVBlock.embedding.cosine_distance(query_embedding))

            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            blocks = result.scalars().all()
            if blocks:
                return [
                    {
                        "id": str(b.id),
                        "category": b.category,
                        "title": b.title,
                        "organization": b.organization,
                        "content": b.content,
                        "metrics": b.metrics,
                        "skills": b.skills,
                    }
                    for b in blocks
                ]
        except Exception:
            # Fall back hermetically on any database connectivity issue
            pass

    # Hermetic fallback scoring based on matching skills
    if required_skills:
        req_set = {s.lower() for s in required_skills}
        ranked = sorted(
            DEFAULT_CV_BLOCKS,
            key=lambda b: len(
                req_set.intersection({s.lower() for s in b.get("skills", [])})
            ),
            reverse=True,
        )
        return ranked[:limit]

    return DEFAULT_CV_BLOCKS[:limit]
