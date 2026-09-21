"""Job search and company intelligence API endpoints."""

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.agents.tools.company_intel import fetch_company_intel
from app.agents.tools.job_search import search_jobs

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class JobSearchRequest(BaseModel):
    """Payload for job discovery query with location and visa sponsorship filters."""

    query: str = Field(..., min_length=2, examples=["Senior AI Engineer"])
    location: str = Field("Remote", examples=["Remote", "San Francisco, CA"])
    visa_required: bool = Field(False, examples=[True, False])


class JobSearchResponse(BaseModel):
    """Response payload containing matching jobs and gathered company dossiers."""

    count: int
    jobs: list[dict[str, Any]]


@router.post(
    "/search",
    response_model=JobSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_and_intel(request: JobSearchRequest) -> JobSearchResponse:
    """Discover jobs and enrich them with target company tech stack intelligence."""
    jobs = await search_jobs(
        query=request.query,
        location=request.location,
        visa_sponsorship_required=request.visa_required,
    )

    enriched_jobs: list[dict[str, Any]] = []
    for job in jobs[:5]:
        company_name = job.get("company_name", "Unknown")
        dossier = await fetch_company_intel(company_name)
        job_copy = dict(job)
        job_copy["company_dossier"] = dossier
        enriched_jobs.append(job_copy)

    return JobSearchResponse(count=len(enriched_jobs), jobs=enriched_jobs)
