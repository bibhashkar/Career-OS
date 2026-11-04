"""
Request and response Pydantic DTOs for job discovery, search, and ingestion.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.search import JobSearchFilterDTO, SearchDiagnosticsDTO
from app.services.matching import JobMatchResult


class JobSearchRequest(BaseModel):
    """
    Payload for job discovery query with location, visa sponsorship,
    and optional command-facet filters.
    """

    query: str = Field("", examples=["Senior AI Engineer"])
    location: str = Field("", examples=["Remote", "San Francisco, CA"])
    visa_required: bool = Field(False, examples=[True, False])
    filters: JobSearchFilterDTO | None = None


class JobSearchResponse(BaseModel):
    """
    Response payload containing matching jobs, gathered company dossiers,
    and zero-dead-end diagnostic relaxation hints.
    """

    count: int
    jobs: list[dict[str, Any]]
    diagnostics: SearchDiagnosticsDTO | None = None


class ParseQueryRequest(BaseModel):
    """Payload for natural language query tokenization."""

    raw_text: str = Field(
        ...,
        examples=["Stripe Senior HealthTech Backend Engineer Remote $180k"],
    )


class IngestJobUrlRequest(BaseModel):
    """Payload for importing a job posting by URL."""

    url: str = Field(
        ...,
        min_length=5,
        examples=["https://boards.greenhouse.io/stripe/jobs/12345"],
    )


class PasteJobTextRequest(BaseModel):
    """Payload for importing a job posting by pasting text."""

    title: str = Field(..., min_length=2, examples=["Senior AI Systems Engineer"])
    company_name: str = Field(..., min_length=2, examples=["Anthropic"])
    raw_description: str = Field(..., min_length=10)
    location: str = Field("Remote", examples=["Remote", "San Francisco, CA"])
    url: str | None = Field(None)
    salary_range: str | None = Field(None, examples=["$180,000 - $220,000"])


class IngestJobResponse(BaseModel):
    """Response payload after importing a job posting."""

    status: str
    message: str
    job: dict[str, Any]


class RefreshCompanyResponse(BaseModel):
    """Response payload for company intelligence refresh."""

    status: str
    refreshed: bool
    message: str
    dossier: dict[str, Any]


class JobMatchesResponse(BaseModel):
    """Paginated response containing matched jobs and active persona metadata."""

    persona_id: str | None = None
    persona_name: str
    total_count: int
    page: int
    page_size: int
    jobs: list[JobMatchResult]
    diagnostics: SearchDiagnosticsDTO | None = None
    profile_ready: bool = True
    profile_status_reason: str | None = None
    completeness: dict[str, Any] | None = None
