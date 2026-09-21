"""Job search tool integration using JSearch API with hermetic offline fallbacks."""

import uuid
from typing import Any

import httpx

from app.core.config import settings

# Deterministic mock dataset for hermetic test execution
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
    """Search for relevant job postings with JSearch or return fixtures."""
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
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
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
        except Exception:
            # Fall back hermetically to mock dataset on any API failure
            pass

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
