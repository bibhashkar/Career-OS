"""
Company intelligence gathering tool with Exa neural search and offline fallbacks.

This tool extracts architectural and business intelligence on prospective employers.
When an ``EXA_API_KEY`` is configured in Settings, it queries the Exa neural search
API to retrieve live engineering blog posts, tech stack disclosures, and press
releases.

Hermetic Offline Fallback:
In CI environments or during local development without paid API keys, network calls
to external search engines are either unconfigured or prone to rate limiting.
This module maintains a deterministic in-memory knowledge base (``MOCK_DOSSIERS``)
of canonical tech companies. If live search is unavailable or fails, it falls back
to these fixtures to ensure tests remain fast, reproducible, and isolated.
"""

import asyncio
import json
import logging
import os
from typing import Any

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.agents.llm import get_llm
from app.core.config import settings
from app.core.database import get_session_context
from app.core.http import DEFAULT_TIMEOUT, execute_with_retry
from app.models.company_dossier import CompanyDossier

logger = logging.getLogger("career_os.tools.company_intel")

# Pre-seeded company intelligence knowledge base for reliable offline testing
MOCK_DOSSIERS: dict[str, dict[str, Any]] = {
    "nexusai labs": {
        "company_name": "NexusAI Labs",
        "domain": "nexusai.example.com",
        "industry": "Artificial Intelligence & RAG",
        "data_origin": "demo",
        "tech_stack": [
            "Python",
            "FastAPI",
            "LangGraph",
            "PostgreSQL",
            "pgvector",
            "Docker",
            "Redis",
        ],
        "recent_news": [
            {
                "title": "NexusAI announces Next-Gen Agent Orchestration Engine",
                "date": "2026-08-15",
                "source": "TechRadar",
            },
            {
                "title": "NexusAI scales pgvector database to 50M records",
                "date": "2026-05-20",
                "source": "VentureBeat",
            },
        ],
        "business_model": "Enterprise multi-agent workflow platform and API",
        "culture_notes": (
            "Fast-paced engineering culture focusing on stateful memory."
        ),
    },
    "scaleagents inc": {
        "company_name": "ScaleAgents Inc",
        "domain": "scaleagents.example.com",
        "industry": "Autonomous Agents",
        "data_origin": "demo",
        "tech_stack": [
            "Python",
            "LangGraph",
            "LangChain",
            "WebSockets",
            "PostgreSQL",
            "Kubernetes",
        ],
        "recent_news": [
            {
                "title": "ScaleAgents achieves sub-50ms conversational agent latency",
                "date": "2026-07-10",
                "source": "AI Weekly",
            }
        ],
        "business_model": "B2B SaaS with usage-based execution tiers",
        "culture_notes": ("Deep technical rigor, high test coverage, async-first."),
    },
}


class CompanyIntelExtractionSchema(BaseModel):
    """Structured extraction of company architecture and engineering culture."""

    industry: str = Field(default="Software Engineering & Technology")
    tech_stack: list[str] = Field(default_factory=list)
    business_model: str = Field(
        default="Enterprise SaaS and cloud automation solutions"
    )
    culture_notes: str = Field(
        default="Focused on modern decoupled architectures and robust DX."
    )


async def fetch_company_intel(
    company_name: str, domain: str | None = None
) -> dict[str, Any]:
    """
    Fetch architectural intelligence and background for a target employer.

    Tries Exa neural search if ``EXA_API_KEY`` is set in environment;
    otherwise returns matching fixtures from ``MOCK_DOSSIERS`` or generates
    a structured profile based on common modern engineering standards.

    Args:
        company_name: Name of the employer (e.g. "NexusAI Labs").
        domain: Optional company web domain (e.g. "nexusai.com").

    Returns:
        Dictionary containing tech_stack, recent_news, business_model, and culture.
    """
    normalized_name = company_name.lower().strip()

    # 1. Query persistent CompanyDossier database cache
    try:
        async with get_session_context() as session:
            stmt = select(CompanyDossier).where(
                func.lower(CompanyDossier.company_name) == normalized_name
            )
            res = await session.execute(stmt)
            cached = res.scalars().first()
            if cached:
                return {
                    "id": str(cached.id),
                    "company_name": cached.company_name,
                    "domain": cached.domain,
                    "industry": cached.industry,
                    "tech_stack": cached.tech_stack,
                    "recent_news": cached.recent_news,
                    "business_model": cached.business_model,
                    "culture_notes": cached.culture_notes,
                    "data_origin": "cached",
                }
    except Exception as exc:
        logger.debug(f"Cache lookup failed for company '{company_name}': {exc}")

    # 2. Match deterministic fixtures for known/demo employers
    if normalized_name in MOCK_DOSSIERS:
        return dict(MOCK_DOSSIERS[normalized_name])

    resolved: dict[str, Any] | None = None
    is_testing = "PYTEST_CURRENT_TEST" in os.environ or settings.APP_ENV == "test"

    # 3. Query Exa neural search if API key configured and not in hermetic test mode
    if settings.EXA_API_KEY and not is_testing:
        try:
            url = "https://api.exa.ai/search"
            headers = {
                "x-api-key": settings.EXA_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "query": f"{company_name} engineering tech stack and recent news",
                "num_results": 3,
                "use_autoprompt": True,
            }

            async def _fetch() -> httpx.Response:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                    return await client.post(url, headers=headers, json=payload)

            resp = await execute_with_retry(
                _fetch,
                max_retries=3,
                operation_name=f"Exa search [{company_name}]",
            )
            if resp and resp.status_code == 200:
                results = resp.json().get("results", [])
                news = [
                    {"title": r.get("title", ""), "url": r.get("url", "")}
                    for r in results
                    if r.get("title")
                ]
                resolved = {
                    "company_name": company_name,
                    "domain": domain or f"{normalized_name.replace(' ', '')}.com",
                    "industry": "Technology",
                    "tech_stack": [],  # Do not invent unverified tech stack
                    "recent_news": news,
                    "business_model": None,
                    "culture_notes": (
                        "Data gathered via live web intelligence search."
                    ),
                    "data_origin": "live",
                }
        except Exception as exc:
            logger.warning(
                f"Exa search failed for company '{company_name}'; falling back: {exc}"
            )

    # 4. Synthesize structured intel via LLM without fabricated news/defaults
    if not resolved:
        mock_json = json.dumps(
            {
                "industry": "Software Engineering & Technology",
                "tech_stack": ["Python", "FastAPI"],
                "business_model": "Software platform services",
                "culture_notes": (
                    "Focused on modern decoupled architectures and robust DX."
                ),
            }
        )
        llm = get_llm(temperature=0.1, default_mock_responses=[mock_json])

        res_industry = "Software Engineering & Technology"
        res_stack: list[str] = []
        res_model: str | None = None
        res_culture: str | None = None

        try:
            chain = llm.with_structured_output(CompanyIntelExtractionSchema)
            llm_output = await asyncio.wait_for(
                chain.ainvoke(
                    [
                        SystemMessage(
                            content=(
                                "You are an enterprise technical profiler. "
                                "Extract the primary tech stack, industry, "
                                "business model, and engineering culture."
                            )
                        ),
                        HumanMessage(content=f"Company: {company_name}"),
                    ]
                ),
                timeout=8.0,
            )
            if isinstance(llm_output, CompanyIntelExtractionSchema):
                res_industry = llm_output.industry or res_industry
                res_stack = llm_output.tech_stack or []
                res_model = llm_output.business_model
                res_culture = llm_output.culture_notes
        except Exception as exc:
            logger.debug(
                f"LLM company intel extraction fallback for '{company_name}': {exc}"
            )

        resolved = {
            "company_name": company_name,
            "domain": domain or f"{normalized_name.replace(' ', '')}.com",
            "industry": res_industry,
            "tech_stack": res_stack,
            "recent_news": [],  # Never fabricate news items
            "business_model": res_model,
            "culture_notes": res_culture,
            "data_origin": "inferred",
        }

    # 4. Persist newly resolved dossier to database
    try:
        async with get_session_context() as session:
            record = CompanyDossier(
                company_name=resolved["company_name"],
                domain=resolved.get("domain"),
                industry=resolved.get("industry"),
                tech_stack=resolved.get("tech_stack", []),
                recent_news=resolved.get("recent_news", []),
                business_model=resolved.get("business_model"),
                culture_notes=resolved.get("culture_notes"),
            )
            session.add(record)
            await session.flush()
            resolved["id"] = str(record.id)
    except Exception as exc:
        logger.warning(
            f"Failed to persist company dossier for "
            f"'{resolved.get('company_name')}': {exc}"
        )

    return resolved
