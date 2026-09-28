"""
Job search and company intelligence API endpoints.

This router powers the job discovery view of the React dashboard. Rather than
requiring the client to make separate round-trips for finding job postings and
then looking up each employer's engineering background, this endpoint executes
an enriched discovery sequence:
  1. Searches job listings matching query, location, and visa sponsorship needs.
  2. For the top results, concurrently gathers company intelligence dossiers
     (tech stack, news, culture, and business model).
  3. Returns unified listings ready for immediate dashboard rendering.
"""

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.agents.tools.company_intel import fetch_company_intel
from app.agents.tools.job_search import search_jobs

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class JobSearchRequest(BaseModel):
    """
    Payload for job discovery query with location and visa sponsorship filters.

    Attributes:
        query: Search keywords or role title (e.g. "Senior AI Systems Engineer").
        location: Geographic filter or "Remote".
        visa_required: When True, filters out listings lacking sponsorship.
    """

    query: str = Field(..., min_length=2, examples=["Senior AI Engineer"])
    location: str = Field("Remote", examples=["Remote", "San Francisco, CA"])
    visa_required: bool = Field(False, examples=[True, False])


class JobSearchResponse(BaseModel):
    """
    Response payload containing matching jobs and gathered company dossiers.

    Attributes:
        count: Number of returned matching job listings.
        jobs: List of job dictionaries, each augmented with a company_dossier.
    """

    count: int
    jobs: list[dict[str, Any]]


@router.post(
    "/search",
    response_model=JobSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_and_intel(request: JobSearchRequest) -> JobSearchResponse:
    """
    Discover jobs and enrich them with target company tech stack intelligence.

    Queries job search providers (JSearch API or offline fixtures) and enriches
    the top 5 matching postings with verified employer tech stacks and company
    dossiers before returning to the frontend.

    Args:
        request: Validated search criteria and constraint filters.

    Returns:
        JobSearchResponse with enriched job listings.
    """
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
