"""
Public Ingestion Boundary API & Domain Ports.

As specified in ARCHITECTURE (unlimited_data_ingestion_plan.md §3), this module
is the ONLY surface that consumer agents (Hunter, Intel, Tailor) may import from.
Agents receive domain DTOs and never raw ORM rows.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import or_, select

from app.agents.tools.company_intel import (
    fetch_company_intel as fallback_fetch_company_intel,
)
from app.agents.tools.job_search import MOCK_JOBS
from app.agents.tools.job_search import search_jobs as mock_search_jobs
from app.core.database import get_session_context
from app.ingestion.company_intel_provider import ProvenanceCompanyIntelProvider
from app.ingestion.models import (
    ATSProvider,
    CompanyDossierDTO,
    DataOrigin,
    DiscoveredJobDTO,
    FieldProvenanceDTO,
    ListingStatus,
    ParsedRequirementsDTO,
    SourceConfidence,
    VisaSponsorshipStatus,
)
from app.models.job_listing import JobListing

logger = logging.getLogger("career_os.ingestion.api")

__all__ = [
    "ATSProvider",
    "CompanyDossierDTO",
    "CompanyIntelPort",
    "DataOrigin",
    "DiscoveredJobDTO",
    "FieldProvenanceDTO",
    "JobListingDTO",
    "JobSourcePort",
    "ListingStatus",
    "LocalJobSourceService",
    "ParsedRequirementsDTO",
    "ProvenanceCompanyIntelService",
    "SourceConfidence",
    "VisaSponsorshipStatus",
    "get_default_company_intel",
    "get_default_job_source",
]


class JobListingDTO(DiscoveredJobDTO):
    """Augmented DTO for fully parsed and registered job listings."""

    id: str | None = None
    url: str | None = None
    visa_sponsorship: VisaSponsorshipStatus = VisaSponsorshipStatus.UNKNOWN
    ats_requirements: dict[str, Any] = {}
    verification: dict[str, Any] = {}


class JobSourcePort(ABC):
    """Port for finding and querying job postings."""

    @abstractmethod
    async def search_jobs(
        self,
        query: str,
        location: str = "Remote",
        visa_required: bool = False,
    ) -> list[JobListingDTO]:
        """Search local and synced job listings."""
        ...

    @abstractmethod
    async def get_job(self, job_id: str) -> JobListingDTO | None:
        """Fetch a specific job listing by unique identifier."""
        ...


class CompanyIntelPort(ABC):
    """Port for employer intelligence."""

    @abstractmethod
    async def get_company_profile(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyDossierDTO:
        """Fetch verified employer intelligence dossier."""
        ...

    @abstractmethod
    async def refresh_company_profile(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyDossierDTO:
        """Force-refresh employer intelligence within cooldown constraints."""
        ...


class LocalJobSourceService(JobSourcePort):
    """
    Concrete implementation of JobSourcePort querying PostgreSQL JobListing records.

    Provides unmetered local search over synced ATS listings with hermetic
    in-memory fallbacks when the database is unavailable or sparse.
    """

    def __init__(self, session_factory=get_session_context) -> None:
        self.session_factory = session_factory

    def _to_dto(self, row: JobListing) -> JobListingDTO:
        data_origin = DataOrigin.LIVE
        if row.data_origin:
            try:
                data_origin = DataOrigin(row.data_origin)
            except ValueError:
                data_origin = DataOrigin.LIVE

        source_conf = SourceConfidence.HIGH
        if row.source_confidence:
            try:
                source_conf = SourceConfidence(row.source_confidence)
            except ValueError:
                source_conf = SourceConfidence.HIGH

        visa_status = VisaSponsorshipStatus.UNKNOWN
        if row.visa_sponsorship:
            try:
                visa_status = VisaSponsorshipStatus(row.visa_sponsorship)
            except ValueError:
                visa_status = VisaSponsorshipStatus.UNKNOWN

        return JobListingDTO(
            id=str(row.id),
            source=row.source,
            source_job_id=row.source_job_id,
            title=row.title,
            company_name=row.company_name,
            url=row.url,
            apply_url=str(row.apply_url or row.url or "https://careers.local"),
            location=row.location,
            salary_range=row.salary_range,
            raw_description=row.raw_description,
            ats_requirements=dict(row.ats_requirements or {}),
            verification=dict(row.verification or {}),
            data_origin=data_origin,
            source_confidence=source_conf,
            visa_sponsorship=visa_status,
            posted_at=row.posted_at,
        )

    def _mock_to_dto(self, m: dict[str, Any]) -> JobListingDTO:
        origin_str = m.get("data_origin", "demo")
        try:
            data_origin = DataOrigin(origin_str)
        except ValueError:
            data_origin = DataOrigin.DEMO

        visa_val = m.get("ats_requirements", {}).get("visa_sponsorship")
        if visa_val is True or visa_val == "yes":
            visa_status = VisaSponsorshipStatus.YES
        elif visa_val is False or visa_val == "no":
            visa_status = VisaSponsorshipStatus.NO
        else:
            visa_status = VisaSponsorshipStatus.UNKNOWN

        return JobListingDTO(
            id=m.get("id"),
            source=m.get("source", "mock_fixture"),
            source_job_id=str(m.get("source_job_id") or m.get("id") or "job-0"),
            title=m.get("title", "Software Engineer"),
            company_name=m.get("company_name", "Unknown Company"),
            url=m.get("url"),
            apply_url=str(
                m.get("apply_url") or m.get("url") or "https://careers.local"
            ),
            location=m.get("location", "Remote"),
            salary_range=m.get("salary_range"),
            raw_description=m.get("raw_description", ""),
            ats_requirements=dict(m.get("ats_requirements") or {}),
            verification=dict(m.get("verification") or {}),
            data_origin=data_origin,
            source_confidence=SourceConfidence.MEDIUM,
            visa_sponsorship=visa_status,
        )

    async def get_job(self, job_id: str) -> JobListingDTO | None:
        try:
            async with self.session_factory() as session:
                stmt = select(JobListing).where(JobListing.source_job_id == job_id)
                try:
                    parsed_uuid = uuid.UUID(str(job_id))
                    stmt = select(JobListing).where(
                        or_(
                            JobListing.id == parsed_uuid,
                            JobListing.source_job_id == job_id,
                        )
                    )
                except (ValueError, TypeError):
                    pass

                result = (await session.execute(stmt)).scalars().first()
                if result:
                    return self._to_dto(result)
        except Exception as exc:
            logger.debug(
                "Database lookup for job '%s' failed or offline: %s", job_id, exc
            )

        for m in MOCK_JOBS:
            if m.get("id") == job_id:
                return self._mock_to_dto(m)
        return None

    async def search_jobs(
        self,
        query: str,
        location: str = "Remote",
        visa_required: bool = False,
    ) -> list[JobListingDTO]:
        try:
            async with self.session_factory() as session:
                query_terms = f"%{query.strip()}%"
                stmt = select(JobListing).where(
                    JobListing.status == "active",
                    or_(
                        JobListing.title.ilike(query_terms),
                        JobListing.company_name.ilike(query_terms),
                        JobListing.raw_description.ilike(query_terms),
                    ),
                )
                if visa_required:
                    stmt = stmt.where(JobListing.visa_sponsorship == "yes")
                if location and location.lower() != "remote":
                    loc_term = f"%{location.strip()}%"
                    stmt = stmt.where(
                        or_(
                            JobListing.location.ilike(loc_term),
                            JobListing.location.ilike("%remote%"),
                        )
                    )
                rows = (
                    (
                        await session.execute(
                            stmt.order_by(JobListing.first_seen_at.desc()).limit(20)
                        )
                    )
                    .scalars()
                    .all()
                )
                if rows:
                    return [self._to_dto(r) for r in rows]
        except Exception as exc:
            logger.debug("Database job search failed or unavailable: %s", exc)

        fallback_raw = await mock_search_jobs(
            query=query,
            location=location,
            visa_sponsorship_required=visa_required,
        )
        return [self._mock_to_dto(m) for m in fallback_raw]


class ProvenanceCompanyIntelService(CompanyIntelPort):
    """
    Concrete implementation of CompanyIntelPort backed by Provenance provider.
    """

    def __init__(self, session_factory=get_session_context) -> None:
        self.session_factory = session_factory

    async def get_company_profile(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyDossierDTO:
        try:
            async with self.session_factory() as session:
                provider = ProvenanceCompanyIntelProvider(session)
                return await provider.fetch_company_intel(
                    company_name=company_name,
                    domain=domain,
                )
        except Exception as exc:
            logger.debug("Provenance company provider query failed: %s", exc)

        raw = await fallback_fetch_company_intel(company_name, domain=domain)
        origin_val = raw.get("data_origin", "demo")
        try:
            d_origin = DataOrigin(origin_val)
        except ValueError:
            d_origin = DataOrigin.DEMO

        return CompanyDossierDTO(
            company_name=raw.get("company_name", company_name),
            canonical_name=raw.get("company_name", company_name),
            domain=raw.get("domain"),
            industry=raw.get("industry"),
            tech_stack=list(raw.get("tech_stack", [])),
            recent_news=list(raw.get("recent_news", [])),
            business_model=raw.get("business_model"),
            culture_notes=raw.get("culture_notes"),
            data_origin=d_origin,
            field_provenance={},
        )

    async def refresh_company_profile(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyDossierDTO:
        return await self.get_company_profile(company_name, domain=domain)


_job_source_instance: JobSourcePort | None = None
_company_intel_instance: CompanyIntelPort | None = None


def get_default_job_source() -> JobSourcePort:
    """Return default application-wide JobSourcePort implementation."""
    global _job_source_instance
    if _job_source_instance is None:
        _job_source_instance = LocalJobSourceService()
    return _job_source_instance


def get_default_company_intel() -> CompanyIntelPort:
    """Return default application-wide CompanyIntelPort implementation."""
    global _company_intel_instance
    if _company_intel_instance is None:
        _company_intel_instance = ProvenanceCompanyIntelService()
    return _company_intel_instance
