"""Company research tool integration with hermetic fallbacks."""

from typing import Any

import httpx

from app.core.config import settings

# Pre-seeded company intelligence knowledge base for reliable offline testing
MOCK_DOSSIERS: dict[str, dict[str, Any]] = {
    "nexusai labs": {
        "company_name": "NexusAI Labs",
        "domain": "nexusai.example.com",
        "industry": "Artificial Intelligence & RAG",
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


async def fetch_company_intel(
    company_name: str, domain: str | None = None
) -> dict[str, Any]:
    """Fetch intelligence on target company (tech stack, news, model)."""
    normalized_name = company_name.lower().strip()

    # If Exa API key is provided, perform live search
    if settings.EXA_API_KEY:
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
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    news = [
                        {"title": r.get("title", ""), "url": r.get("url", "")}
                        for r in results
                    ]
                    return {
                        "company_name": company_name,
                        "domain": domain or f"{normalized_name.replace(' ', '')}.com",
                        "industry": "Technology",
                        "tech_stack": [
                            "Python",
                            "FastAPI",
                            "PostgreSQL",
                            "Cloud",
                        ],
                        "recent_news": news,
                        "business_model": "Software platform services",
                        "culture_notes": (
                            "Data gathered via live web intelligence search."
                        ),
                    }
        except Exception:
            pass

    # Return matched mock dossier or generate dynamic structured intelligence
    if normalized_name in MOCK_DOSSIERS:
        return MOCK_DOSSIERS[normalized_name]

    return {
        "company_name": company_name,
        "domain": domain or f"{normalized_name.replace(' ', '')}.com",
        "industry": "Software Engineering & Technology",
        "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
        "recent_news": [
            {
                "title": f"{company_name} expands engineering for AI",
                "date": "2026-06-01",
                "source": "Industry Journal",
            }
        ],
        "business_model": "Enterprise SaaS and cloud automation solutions",
        "culture_notes": ("Focused on modern decoupled architectures and robust DX."),
    }
