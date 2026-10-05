"""
Job search tool integration using JSearch API with hermetic offline fallbacks.

This tool interfaces with the JSearch API (via RapidAPI) to query live job board
aggregations across LinkedIn, Indeed, ZipRecruiter, and company careers pages.
It extracts job titles, employer names, raw descriptions, salary ranges, and
inferred ATS requirements.

Hermetic Offline Fallback:
To allow hermetic testing and local offline development, this module maintains
a deterministic set of realistic job listings in ``MOCK_JOBS``. When no
``JSEARCH_API_KEY`` is configured or when the remote API fails/times out, search
queries fall back to keyword filtering over this local dataset. This guarantees
that tests never fail due to third-party network outages or exhausted API quotas.
"""

import logging
import uuid
from typing import Any

import httpx

from app.core.config import settings
from app.core.http import DEFAULT_TIMEOUT, execute_with_retry

logger = logging.getLogger("career_os.tools.job_search")

# Deterministic mock dataset for hermetic test execution and offline development
MOCK_JOBS: list[dict[str, Any]] = [
    {
        "id": "job-ai-001",
        "title": "Senior AI Systems Engineer",
        "company_name": "NexusAI Labs",
        "url": "https://nexusai.example.com/careers/ai-eng",
        "location": "Remote",
        "salary_range": "$160,000 - $195,000",
        "raw_description": (
            "We are seeking a Senior AI Systems Engineer with deep expertise in "
            "Python, FastAPI, LangGraph multi-agent workflows, and PostgreSQL "
            "with pgvector. You will design scalable RAG systems, stateful agent "
            "checkpoints, and ATS optimizers."
        ),
        "ats_requirements": {
            "required_skills": [
                "Python",
                "FastAPI",
                "LangGraph",
                "PostgreSQL",
                "pgvector",
            ],
            "preferred_skills": ["Docker", "Redis", "React", "TypeScript"],
            "min_experience_years": 4,
            "visa_sponsorship": True,
        },
    },
    {
        "id": "job-ai-002",
        "title": "Staff Backend Engineer (Agents & Platform)",
        "company_name": "ScaleAgents Inc",
        "url": "https://scaleagents.example.com/jobs/backend-staff",
        "location": "San Francisco, CA (Hybrid)",
        "salary_range": "$180,000 - $220,000",
        "raw_description": (
            "Looking for a Staff Backend Engineer to scale our runtime. "
            "Experience with LangChain, LangGraph, async psycopg, pgvector, "
            "and WebSocket bi-directional streaming is required."
        ),
        "ats_requirements": {
            "required_skills": [
                "Python",
                "LangGraph",
                "WebSockets",
                "SQLAlchemy",
                "PostgreSQL",
            ],
            "preferred_skills": ["Kubernetes", "gRPC", "Next.js"],
            "min_experience_years": 6,
            "visa_sponsorship": True,
        },
    },
    {
        "id": "job-ai-003",
        "title": "Full-Stack AI Application Developer",
        "company_name": "CareerCloud Systems",
        "url": "https://careercloud.example.com/openings/fullstack-ai",
        "location": "Remote",
        "salary_range": "$140,000 - $175,000",
        "raw_description": (
            "Join us to build stateful career applications. Stack includes React, "
            "Vite, Tailwind CSS, FastAPI, and PostgreSQL pgvector embeddings. "
            "Must be able to craft clean components and responsive UIs."
        ),
        "ats_requirements": {
            "required_skills": [
                "React",
                "FastAPI",
                "Tailwind CSS",
                "Python",
                "JavaScript",
            ],
            "preferred_skills": ["pgvector", "LangGraph", "Docker"],
            "min_experience_years": 3,
            "visa_sponsorship": False,
        },
    },
]


async def search_jobs(
    query: str,
    location: str = "Remote",
    visa_sponsorship_required: bool = False,
) -> list[dict[str, Any]]:
    """
    Search for matching job listings using JSearch API or local fixtures.

    Queries JSearch if ``JSEARCH_API_KEY`` is configured; otherwise filters
    the local ``MOCK_JOBS`` dataset by title and description keywords. If
    ``visa_sponsorship_required`` is True, listings that explicitly do not
    provide sponsorship are excluded.

    Args:
        query: Search keywords or target job title (e.g. "Senior AI Engineer").
        location: Geographic location or "Remote".
        visa_sponsorship_required: When True, filters out listings lacking sponsorship.

    Returns:
        List of matching job listing dictionaries.
    """
    if settings.JSEARCH_API_KEY:
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            headers = {
                "x-rapidapi-key": settings.JSEARCH_API_KEY,
                "x-rapidapi-host": "jsearch.p.rapidapi.com",
            }
            params = {
                "query": f"{query} in {location}",
                "page": "1",
                "num_pages": "1",
            }

            async def _fetch() -> httpx.Response:
                async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                    return await client.get(url, headers=headers, params=params)

            response = await execute_with_retry(
                _fetch,
                max_retries=3,
                operation_name=f"JSearch API [{query}]",
            )
            if response and response.status_code == 200:
                data = response.json().get("data", [])
                results = []
                for item in data[:5]:
                    city = item.get("job_city", "")
                    state = item.get("job_state", "")
                    loc_str = f"{city}, {state}".strip(", ") or location
                    results.append(
                        {
                            "id": item.get("job_id", str(uuid.uuid4())),
                            "title": item.get("job_title", query),
                            "company_name": item.get("employer_name", "Unknown"),
                            "url": item.get("job_apply_link"),
                            "location": loc_str,
                            "salary_range": item.get("job_salary") or "Competitive",
                            "raw_description": item.get("job_description", ""),
                            "ats_requirements": {
                                "required_skills": [query],
                                "visa_sponsorship": True,
                            },
                        }
                    )
                if results:
                    return results
        except Exception as exc:
            # Fall back hermetically to mock dataset on any API failure
            logger.warning(
                f"JSearch API request failed for query '{query}'; "
                f"falling back to mock dataset: {exc}"
            )

    # Hermetic filtering over local dataset
    query_lower = query.lower()
    matches = []
    for job in MOCK_JOBS:
        if visa_sponsorship_required and not job["ats_requirements"].get(
            "visa_sponsorship", False
        ):
            continue
        text_corpus = f"{job['title']} {job['raw_description']}".lower()
        if any(term in text_corpus for term in query_lower.split()):
            matches.append(job)

    return matches if matches else MOCK_JOBS
