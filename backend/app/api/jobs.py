"""
Job search, manual ingestion, and company intelligence API endpoints.

This router powers the job discovery and ingestion view of Career-OS:
  1. Sync-then-Search: Queries local synced ATS listings first (unmetered, zero
     external rate limits) before falling back to external search.
  2. Manual Ingestion: Ingest by direct ATS URL (Greenhouse, Lever, Ashby) or
     pasting raw job text with automatic grounding requirements extraction.
  3. Secondary Cross-Check: Cross-checks selected jobs against aggregators
     while strictly preserving ATS data as authoritative.
  4. Company Intelligence: Enriches roles with provenance-tracked dossiers and
     provides manual refresh with cooldown enforcement.
"""

import asyncio
import logging
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select

from app.agents.tools.company_intel import fetch_company_intel
from app.agents.tools.job_search import search_jobs
from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.database import get_session_context
from app.ingestion.adapters.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter
from app.ingestion.company_intel_provider import ProvenanceCompanyIntelProvider
from app.ingestion.discovery import BoardDiscoveryEngine
from app.ingestion.extractor import HybridRequirementsExtractor
from app.ingestion.models import ATSProvider, DataOrigin, SourceConfidence
from app.ingestion.security import (
    SecurityValidationError,
    parse_ats_url,
    sanitize_text,
    validate_and_guard_url,
)
from app.ingestion.service import compute_content_hash, compute_dedupe_fingerprint
from app.ingestion.verification import JobVerificationService
from app.models.company_dossier import CompanyDossier
from app.models.job_listing import JobListing

logger = logging.getLogger("career_os.jobs")

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class JobSearchRequest(BaseModel):
    """
    Payload for job discovery query with location and visa sponsorship filters.
    """

    query: str = Field("", examples=["Senior AI Engineer"])
    location: str = Field("", examples=["Remote", "San Francisco, CA"])
    visa_required: bool = Field(False, examples=[True, False])


class JobSearchResponse(BaseModel):
    """
    Response payload containing matching jobs and gathered company dossiers.
    """

    count: int
    jobs: list[dict[str, Any]]


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


def _format_job_dict(
    job: JobListing, dossier: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Format JobListing ORM row into an enriched dictionary with provenance."""
    return {
        "id": str(job.id),
        "title": job.title,
        "company_name": job.company_name,
        "url": job.url,
        "apply_url": job.apply_url or job.url,
        "location": job.raw_location,
        "raw_location": job.raw_location,
        "city": job.city,
        "state_province": job.state_province,
        "state_province_code": job.state_province_code,
        "country": job.country,
        "country_code": job.country_code,
        "primary_region": job.primary_region,
        "workplace_type": job.workplace_type,
        "remote_scope": job.remote_scope,
        "remote_type": "Remote"
        if job.workplace_type == "remote"
        else ("Hybrid" if job.workplace_type == "hybrid" else "On-site"),
        "salary_range": job.salary_range,
        "raw_description": job.raw_description,
        "ats_requirements": job.ats_requirements or {},
        "ats_provider": job.ats_provider,
        "ats_board_slug": job.ats_board_slug,
        "source": f"{job.ats_provider}:{job.ats_board_slug}",
        "source_confidence": job.source_confidence,
        "data_origin": job.data_origin,
        "visa_sponsorship": job.visa_sponsorship,
        "visa_notes": job.visa_notes,
        "visa_types": job.visa_types or [],
        "industry": job.industry,
        "verification": job.verification or {},
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "company_dossier": dossier,
    }


@router.post(
    "/search",
    response_model=JobSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_and_intel(
    request: JobSearchRequest,
    user: CurrentUser,
) -> JobSearchResponse:
    """
    Discover jobs using Sync-then-Search architecture:
      1. Queries local synced ATS listings first (anti-fragile, zero external quota).
      2. If local matches are sparse (< 5), executes budgeted external search fallback.
      3. Snowballs external results into tier-1 ATS boards when apply URLs match.
      4. Concurrently enriches jobs with employer intelligence and provenance badges.
    """
    enriched_jobs: list[dict[str, Any]] = []

    clean_query = request.query.strip()
    clean_location = request.location.strip()

    # Fast path: If both query and location are empty or whitespace,
    # return empty results immediately
    if not clean_query and not clean_location:
        return JobSearchResponse(count=0, jobs=[])

    try:
        async with get_session_context() as session:
            # Step 1: Query local synced jobs
            stmt = select(JobListing).where(JobListing.status == "active")

            if clean_query:
                query_terms = f"%{clean_query}%"
                stmt = stmt.where(
                    or_(
                        JobListing.title.ilike(query_terms),
                        JobListing.company_name.ilike(query_terms),
                        JobListing.raw_description.ilike(query_terms),
                    )
                )

            if request.visa_required:
                stmt = stmt.where(JobListing.visa_sponsorship == "yes")

            if clean_location and clean_location.lower() != "remote":
                loc_term = f"%{clean_location}%"
                stmt = stmt.where(
                    or_(
                        JobListing.raw_location.ilike(loc_term),
                        JobListing.city.ilike(loc_term),
                        JobListing.state_province.ilike(loc_term),
                        JobListing.state_province_code.ilike(loc_term),
                        JobListing.country.ilike(loc_term),
                        JobListing.country_code.ilike(loc_term),
                        JobListing.workplace_type == "remote",
                    )
                )
            elif clean_location.lower() == "remote":
                stmt = stmt.where(
                    or_(
                        JobListing.workplace_type == "remote",
                        JobListing.raw_location.ilike("%remote%"),
                    )
                )

            local_matches = (
                (
                    await session.execute(
                        stmt.order_by(JobListing.first_seen_at.desc()).limit(10)
                    )
                )
                .scalars()
                .all()
            )

            for j in local_matches:
                dossier_data: dict[str, Any] | None = None
                if j.company_dossier:
                    dossier_data = {
                        "id": str(j.company_dossier.id),
                        "company_name": j.company_dossier.company_name,
                        "domain": j.company_dossier.domain,
                        "industry": j.company_dossier.industry,
                        "tech_stack": j.company_dossier.tech_stack,
                        "recent_news": j.company_dossier.recent_news,
                        "business_model": j.company_dossier.business_model,
                        "culture_notes": j.company_dossier.culture_notes,
                        "data_origin": j.company_dossier.data_origin,
                        "field_provenance": j.company_dossier.field_provenance,
                    }
                enriched_jobs.append(_format_job_dict(j, dossier=dossier_data))
    except Exception as exc:
        logger.warning("Local job query failed or DB offline: %s", exc)

    # Step 2: Fallback to external search ONLY when configured with
    # real key or running test suite
    is_test = "pytest" in sys.modules or settings.APP_ENV == "test"
    should_fallback = (
        len(enriched_jobs) < 5
        and bool(clean_query)
        and (bool(settings.JSEARCH_API_KEY) or is_test)
    )

    if should_fallback:
        fallback_jobs = await search_jobs(
            query=clean_query,
            location=clean_location or "Remote",
            visa_sponsorship_required=request.visa_required,
        )

        if not is_test:
            # Never return mock/demo jobs to users in non-test environments
            fallback_jobs = [j for j in fallback_jobs if j.get("data_origin") != "demo"]

        existing_titles = {j["title"].lower() for j in enriched_jobs}
        top_fallback = [
            j
            for j in fallback_jobs
            if j.get("title", "").lower() not in existing_titles
        ][: (5 - len(enriched_jobs))]

        dossiers = await asyncio.gather(
            *(
                fetch_company_intel(j.get("company_name", "Unknown"))
                for j in top_fallback
            )
        )

        try:
            async with get_session_context() as session:
                discovery = BoardDiscoveryEngine(session)
                for raw_job, dossier in zip(top_fallback, dossiers, strict=True):
                    # Never persist demo jobs into PostgreSQL
                    if raw_job.get("data_origin") == "demo":
                        if is_test:
                            # In test mode, keep in memory only
                            job_copy = dict(raw_job)
                            job_copy["company_dossier"] = dossier
                            if "id" not in job_copy:
                                job_copy["id"] = str(uuid.uuid4())
                            job_copy.setdefault("source_confidence", "medium")
                            job_copy.setdefault("verification", {})
                            job_copy.setdefault(
                                "visa_sponsorship",
                                (
                                    "yes"
                                    if job_copy.get("ats_requirements", {}).get(
                                        "visa_sponsorship"
                                    )
                                    else "unknown"
                                ),
                            )
                            enriched_jobs.append(job_copy)
                        continue

                    job_copy = dict(raw_job)
                    job_copy["company_dossier"] = dossier

                    # Attempt to register board via snowballing if URL is a known ATS
                    job_url = raw_job.get("url") or ""
                    parsed_ats = parse_ats_url(job_url)
                    if parsed_ats:
                        ats_prov, ats_slug, _ = parsed_ats
                        try:
                            await discovery.register_board_if_not_exists(
                                provider=ats_prov,
                                slug=ats_slug,
                                company_name=raw_job.get("company_name", "Unknown"),
                                discovered_via="snowball",
                            )
                        except Exception as disc_err:
                            logger.debug(
                                "Board snowball registration skipped: %s", disc_err
                            )

                    # Persist discovered job
                    dossier_id = None
                    if dossier and dossier.get("id"):
                        try:
                            dossier_id = uuid.UUID(str(dossier["id"]))
                        except (ValueError, TypeError):
                            dossier_id = None

                    fingerprint = compute_dedupe_fingerprint(
                        job_copy.get("company_name", ""),
                        job_copy.get("title", ""),
                        job_copy.get("location", "Remote"),
                    )
                    content_hash = compute_content_hash(
                        job_copy.get("raw_description", "")
                    )
                    visa_status = (
                        "yes"
                        if job_copy.get("ats_requirements", {}).get("visa_sponsorship")
                        else "unknown"
                    )

                    from app.ingestion.taxonomy import (
                        LocationNormalizer,
                        VisaSponsorshipParser,
                    )

                    raw_loc = job_copy.get("location") or "Remote"
                    loc_info = LocationNormalizer().normalize(raw_loc)
                    visa_info = VisaSponsorshipParser().parse(
                        job_copy.get("raw_description", "")
                    )

                    source_id = str(job_copy.get("id") or uuid.uuid4().hex[:16])
                    clean_comp = job_copy.get("company_name", "Unknown Company")

                    from app.ingestion.service import BoardSyncService

                    sync_service = BoardSyncService(session)
                    board = await sync_service.get_or_create_board(
                        "custom", f"agg_{clean_comp.lower()[:20]}"
                    )

                    stmt = select(JobListing).where(
                        JobListing.ats_provider == "custom",
                        JobListing.ats_board_slug == board.slug,
                        JobListing.source_job_id == source_id,
                    )
                    existing_rec = (await session.execute(stmt)).scalar_one_or_none()

                    if existing_rec is None:
                        job_record = JobListing(
                            ats_board_id=board.id,
                            ats_provider="custom",
                            ats_board_slug=board.slug,
                            source_job_id=source_id,
                            industry=board.industry or "enterprise_saas",
                            company_dossier_id=dossier_id,
                            title=job_copy.get("title", "Unknown Role"),
                            company_name=clean_comp,
                            url=job_copy.get("url"),
                            apply_url=job_copy.get("url"),
                            raw_location=raw_loc,
                            city=loc_info.city,
                            state_province=loc_info.state_province,
                            state_province_code=loc_info.state_province_code,
                            country=loc_info.country,
                            country_code=loc_info.country_code,
                            primary_region=loc_info.primary_region
                            or board.primary_region,
                            workplace_type=loc_info.workplace_type.value
                            if hasattr(loc_info.workplace_type, "value")
                            else str(loc_info.workplace_type),
                            remote_scope=loc_info.remote_scope.value
                            if hasattr(loc_info.remote_scope, "value")
                            else str(loc_info.remote_scope),
                            salary_range=job_copy.get("salary_range"),
                            raw_description=job_copy.get("raw_description", ""),
                            ats_requirements=job_copy.get("ats_requirements", {}),
                            data_origin=job_copy.get("data_origin", "live"),
                            source_confidence=job_copy.get(
                                "source_confidence", "medium"
                            ),
                            visa_sponsorship=visa_info.status or visa_status,
                            visa_notes=visa_info.notes,
                            visa_types=visa_info.visa_types,
                            fingerprint=fingerprint,
                            content_hash=content_hash,
                            status="active",
                        )
                        session.add(job_record)
                        await session.flush()
                        job_copy["id"] = str(job_record.id)
                    else:
                        job_copy["id"] = str(existing_rec.id)

                    job_copy["data_origin"] = job_copy.get("data_origin", "live")
                    job_copy["source_confidence"] = job_copy.get(
                        "source_confidence", "medium"
                    )
                    job_copy["visa_sponsorship"] = visa_status
                    job_copy["verification"] = job_copy.get("verification", {})
                    enriched_jobs.append(job_copy)
        except Exception as exc:
            logger.warning("Failed to persist fallback jobs: %s", exc)
            for raw_job, dossier in zip(top_fallback, dossiers, strict=True):
                if raw_job.get("data_origin") == "demo" and settings.APP_ENV != "test":
                    continue
                job_copy = dict(raw_job)
                job_copy["company_dossier"] = dossier
                if "id" not in job_copy:
                    job_copy["id"] = str(uuid.uuid4())
                job_copy.setdefault("data_origin", "live")
                job_copy.setdefault("source_confidence", "medium")
                job_copy.setdefault("verification", {})
                job_copy.setdefault(
                    "visa_sponsorship",
                    (
                        "yes"
                        if job_copy.get("ats_requirements", {}).get("visa_sponsorship")
                        else "unknown"
                    ),
                )
                enriched_jobs.append(job_copy)

    # Attach dossiers for any local jobs lacking them
    missing_dossier_jobs = [j for j in enriched_jobs if not j.get("company_dossier")]
    if missing_dossier_jobs:
        fetched_dossiers = await asyncio.gather(
            *(fetch_company_intel(j["company_name"]) for j in missing_dossier_jobs)
        )
        for job, dossier in zip(missing_dossier_jobs, fetched_dossiers, strict=True):
            job["company_dossier"] = dossier

    return JobSearchResponse(count=len(enriched_jobs), jobs=enriched_jobs)


@router.post(
    "/ingest-url",
    response_model=IngestJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_job_from_url(
    request: IngestJobUrlRequest,
    user: CurrentUser,
) -> IngestJobResponse:
    """
    Ingest a job posting from a supported careers URL (Greenhouse, Lever, Ashby).

    Follows 'parse, don't fetch' security rule: regexes out provider, slug, and job_id
    and queries canonical API hosts, eliminating SSRF vulnerabilities by construction.
    """
    parsed = parse_ats_url(request.url)
    if not parsed:
        # Validate URL to catch SSRF attempts even on unsupported URLs
        try:
            validate_and_guard_url(request.url, resolve_dns=False)
        except SecurityValidationError as sec_err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security validation failed: {sec_err}",
            ) from sec_err
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Direct URL ingestion supports Greenhouse, Lever, and Ashby postings. "
                "For other career portals or LinkedIn, please use the 'Paste Job' tab."
            ),
        )

    provider, slug, job_id = parsed
    if not job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Posting URL does not contain a specific job identifier.",
        )

    adapter_map = {
        ATSProvider.GREENHOUSE: GreenhouseAdapter(),
        ATSProvider.LEVER: LeverAdapter(),
        ATSProvider.ASHBY: AshbyAdapter(),
    }
    adapter = adapter_map.get(provider)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported ATS provider: {provider}",
        )

    job_dto = await adapter.fetch_job_detail(slug, job_id)
    if not job_dto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Job posting {job_id} not found on {provider} board '{slug}'."),
        )

    # Extract requirements
    extractor = HybridRequirementsExtractor()
    reqs = await extractor.extract_requirements(
        title=job_dto.title,
        raw_description=job_dto.raw_description,
        company_name=job_dto.company_name,
    )

    now = datetime.now(UTC)
    fingerprint = compute_dedupe_fingerprint(
        job_dto.company_name, job_dto.title, job_dto.raw_location
    )
    content_hash = compute_content_hash(job_dto.raw_description)

    modality = (
        job_dto.workplace_type.value
        if hasattr(job_dto.workplace_type, "value")
        else str(job_dto.workplace_type)
    )
    scope = (
        job_dto.remote_scope.value
        if hasattr(job_dto.remote_scope, "value")
        else str(job_dto.remote_scope)
    )

    async with get_session_context() as session:
        # Register or get board in ats_board table
        discovery = BoardDiscoveryEngine(session)
        board = await discovery.register_board_if_not_exists(
            provider=provider,
            slug=slug,
            company_name=job_dto.company_name,
            discovered_via="url_ingest",
        )
        if not board:
            from app.ingestion.service import BoardSyncService

            sync_service = BoardSyncService(session)
            board = await sync_service.get_or_create_board(provider, slug)

        job_industry = board.industry or job_dto.industry or "enterprise_saas"

        # Upsert job listing
        stmt = select(JobListing).where(
            JobListing.ats_provider == job_dto.ats_provider,
            JobListing.ats_board_slug == job_dto.ats_board_slug,
            JobListing.source_job_id == job_dto.source_job_id,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing is None:
            job_record = JobListing(
                ats_board_id=board.id,
                ats_provider=job_dto.ats_provider,
                ats_board_slug=job_dto.ats_board_slug,
                source_job_id=job_dto.source_job_id,
                industry=job_industry,
                company_dossier_id=board.company_dossier_id,
                title=job_dto.title,
                company_name=board.company_name or job_dto.company_name,
                apply_url=job_dto.apply_url,
                url=job_dto.apply_url,
                raw_location=job_dto.raw_location,
                city=job_dto.city,
                state_province=job_dto.state_province,
                state_province_code=job_dto.state_province_code,
                country=job_dto.country,
                country_code=job_dto.country_code,
                primary_region=job_dto.primary_region or board.primary_region,
                workplace_type=modality,
                remote_scope=scope,
                salary_range=job_dto.salary_range,
                raw_description=job_dto.raw_description,
                posted_at=job_dto.posted_at,
                first_seen_at=now,
                last_seen_at=now,
                last_fetched_at=now,
                fingerprint=fingerprint,
                content_hash=content_hash,
                status="active",
                data_origin=str(DataOrigin.LIVE),
                source_confidence=str(SourceConfidence.HIGH),
                visa_sponsorship=job_dto.visa_sponsorship or str(reqs.visa_sponsorship),
                visa_notes=job_dto.visa_notes,
                visa_types=job_dto.visa_types,
                ats_requirements=reqs.model_dump(),
                verification={},
            )
            session.add(job_record)
            await session.flush()
        else:
            job_record = existing
            job_record.last_seen_at = now
            job_record.last_fetched_at = now
            job_record.raw_description = job_dto.raw_description
            job_record.ats_requirements = reqs.model_dump()
            if job_dto.visa_sponsorship:
                job_record.visa_sponsorship = job_dto.visa_sponsorship
            job_record.workplace_type = modality
            job_record.remote_scope = scope
            job_record.raw_location = job_dto.raw_location
            if job_dto.city:
                job_record.city = job_dto.city
            if job_dto.state_province_code:
                job_record.state_province_code = job_dto.state_province_code
            if job_dto.country_code:
                job_record.country_code = job_dto.country_code
            job_record.status = "active"
            await session.flush()

        # Fetch or link company dossier
        dossier = await fetch_company_intel(job_dto.company_name)
        result_dict = _format_job_dict(job_record, dossier=dossier)

    return IngestJobResponse(
        status="success",
        message=f"Job '{job_dto.title}' successfully ingested from {provider}.",
        job=result_dict,
    )


@router.post(
    "/paste-text",
    response_model=IngestJobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def paste_job_text(
    request: PasteJobTextRequest,
    user: CurrentUser,
) -> IngestJobResponse:
    """
    Ingest a job posting by pasting the job title, company name, and full description.

    Applies text sanitization, extracts requirements with grounding verification,
    and stores the job with data_origin='manual'.
    """
    clean_title = sanitize_text(request.title)
    clean_company = sanitize_text(request.company_name)
    clean_location = sanitize_text(request.location)
    clean_desc = sanitize_text(request.raw_description)

    extractor = HybridRequirementsExtractor()
    reqs = await extractor.extract_requirements(
        title=clean_title,
        raw_description=clean_desc,
        company_name=clean_company,
    )

    now = datetime.now(UTC)
    source_id = f"manual_{uuid.uuid4().hex[:12]}"
    fingerprint = compute_dedupe_fingerprint(clean_company, clean_title, clean_location)
    content_hash = compute_content_hash(clean_desc)

    from app.ingestion.taxonomy import LocationNormalizer, VisaSponsorshipParser

    loc_norm = LocationNormalizer()
    loc_info = loc_norm.normalize(clean_location)

    visa_parser = VisaSponsorshipParser()
    visa_info = visa_parser.parse(clean_desc)

    async with get_session_context() as session:
        # Link to custom/manual ATSBoard
        from app.ingestion.service import BoardSyncService

        sync_service = BoardSyncService(session)
        board = await sync_service.get_or_create_board(
            "custom", f"manual_{clean_company.lower()[:20]}"
        )

        job_record = JobListing(
            ats_board_id=board.id,
            ats_provider="custom",
            ats_board_slug=board.slug,
            source_job_id=source_id,
            industry=board.industry or "enterprise_saas",
            company_dossier_id=board.company_dossier_id,
            title=clean_title,
            company_name=clean_company,
            url=request.url,
            apply_url=request.url,
            raw_location=clean_location,
            city=loc_info.city,
            state_province=loc_info.state_province,
            state_province_code=loc_info.state_province_code,
            country=loc_info.country,
            country_code=loc_info.country_code,
            primary_region=loc_info.primary_region or board.primary_region,
            workplace_type=loc_info.workplace_type.value
            if hasattr(loc_info.workplace_type, "value")
            else str(loc_info.workplace_type),
            remote_scope=loc_info.remote_scope.value
            if hasattr(loc_info.remote_scope, "value")
            else str(loc_info.remote_scope),
            salary_range=request.salary_range,
            raw_description=clean_desc,
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            fingerprint=fingerprint,
            content_hash=content_hash,
            status="active",
            data_origin=str(DataOrigin.MANUAL),
            source_confidence=str(SourceConfidence.HIGH),
            visa_sponsorship=visa_info.status or str(reqs.visa_sponsorship),
            visa_notes=visa_info.notes,
            visa_types=visa_info.visa_types,
            ats_requirements=reqs.model_dump(),
            verification={},
        )
        session.add(job_record)
        await session.flush()

        dossier = await fetch_company_intel(clean_company)
        result_dict = _format_job_dict(job_record, dossier=dossier)

    return IngestJobResponse(
        status="success",
        message="Manual job posting parsed and created successfully.",
        job=result_dict,
    )


@router.post(
    "/companies/{company_name}/refresh",
    response_model=RefreshCompanyResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_company_intel(
    company_name: str,
    user: CurrentUser,
) -> RefreshCompanyResponse:
    """
    Manually trigger company intelligence refresh with cooldown enforcement (1 hour).
    """
    clean_name = sanitize_text(company_name)
    now = datetime.now(UTC)

    async with get_session_context() as session:
        stmt = select(CompanyDossier).where(
            CompanyDossier.company_name.ilike(clean_name)
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing and existing.last_fetched_at:
            last_fetched = existing.last_fetched_at
            if last_fetched.tzinfo is None:
                last_fetched = last_fetched.replace(tzinfo=UTC)
            time_since_fetch = now - last_fetched
            if time_since_fetch < timedelta(hours=1):
                dossier_dict = {
                    "id": str(existing.id),
                    "company_name": existing.company_name,
                    "domain": existing.domain,
                    "industry": existing.industry,
                    "tech_stack": existing.tech_stack,
                    "recent_news": existing.recent_news,
                    "business_model": existing.business_model,
                    "culture_notes": existing.culture_notes,
                    "data_origin": existing.data_origin,
                    "field_provenance": existing.field_provenance,
                }
                return RefreshCompanyResponse(
                    status="cooldown",
                    refreshed=False,
                    message="Company intel recently refreshed. Cooldown is active.",
                    dossier=dossier_dict,
                )

        provider = ProvenanceCompanyIntelProvider(session)
        dto = await provider.fetch_company_intel(clean_name)

        stmt_after = select(CompanyDossier).where(
            CompanyDossier.company_name.ilike(clean_name)
        )
        dossier_record = (await session.execute(stmt_after)).scalar_one_or_none()
        dossier_id = str(dossier_record.id) if dossier_record else str(uuid.uuid4())

        dossier_dict = {
            "id": dossier_id,
            "company_name": dto.company_name,
            "domain": dto.domain,
            "industry": dto.industry,
            "tech_stack": dto.tech_stack,
            "recent_news": dto.recent_news,
            "business_model": dto.business_model,
            "culture_notes": dto.culture_notes,
            "data_origin": str(dto.data_origin),
            "field_provenance": {
                k: v.model_dump(mode="json") for k, v in dto.field_provenance.items()
            },
        }

    return RefreshCompanyResponse(
        status="refreshed",
        refreshed=True,
        message="Company intelligence refreshed successfully.",
        dossier=dossier_dict,
    )


@router.post(
    "/{job_id}/cross-check",
    status_code=status.HTTP_200_OK,
)
async def cross_check_job(
    job_id: str,
    user: CurrentUser,
) -> dict[str, Any]:
    """
    Perform secondary aggregator cross-check on a selected job posting.

    Reconciles salary or listing status discrepancies without overwriting ATS data.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for job_id.",
        ) from err

    async with get_session_context() as session:
        verifier = JobVerificationService(session)
        try:
            verification_result = await verifier.verify_job(job_uuid, force=True)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    return {
        "status": "success",
        "job_id": job_id,
        "verification": verification_result,
    }
