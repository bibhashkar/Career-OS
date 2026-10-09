"""
Public Ingestion Boundary API & Domain Ports.

As specified in ARCHITECTURE (unlimited_data_ingestion_plan.md §3), this module
is the ONLY surface that consumer agents (Hunter, Intel, Tailor) may import from.
Agents receive domain DTOs and never raw ORM rows.
"""

from abc import ABC, abstractmethod
from typing import Any

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
    "ParsedRequirementsDTO",
    "SourceConfidence",
    "VisaSponsorshipStatus",
]


class JobListingDTO(DiscoveredJobDTO):
    """Augmented DTO for fully parsed and registered job listings."""

    id: str | None = None
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
