"""
Port interfaces for ingestion providers, rate limiting, and repositories.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.ingestion.models import (
    ATSProvider,
    CompanyDossierDTO,
    DiscoveredJobDTO,
    ParsedRequirementsDTO,
)


class ATSAdapterPort(ABC):
    """
    Port for ATS board adapters (Greenhouse, Lever, Ashby, etc.).

    Implementations provide canonical extraction directly from official ATS APIs.
    """

    @property
    @abstractmethod
    def provider(self) -> ATSProvider:
        """The ATS provider identity."""
        pass

    @abstractmethod
    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        """Fetch all currently open job postings for a company board slug."""
        pass

    @abstractmethod
    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        """Fetch full details and description for a specific job posting."""
        pass


class RequirementsExtractorPort(ABC):
    """
    Port for extracting structured ATS requirements from job descriptions.
    """

    @abstractmethod
    async def extract_requirements(
        self,
        title: str,
        raw_description: str,
        company_name: str,
    ) -> ParsedRequirementsDTO:
        """Extract required/preferred skills, visa policy, and years of experience."""
        pass


class CompanyIntelProviderPort(ABC):
    """
    Port for sourcing company dossier intelligence with provenance.
    """

    @abstractmethod
    async def fetch_company_intel(
        self,
        company_name: str,
        domain: str | None = None,
        job_description: str | None = None,
    ) -> CompanyDossierDTO:
        """Retrieve verified company intelligence."""
        pass


class CompanyContactProviderPort(ABC):
    """
    Port stub for commercial contact / recruiter lookups (Decision D3).

    Reserved for future Apollo / LinkedIn recruiter integrations.
    """

    @abstractmethod
    async def fetch_contacts(
        self,
        company_name: str,
        domain: str | None = None,
        role_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch recruiter or hiring team contact records."""
        pass


class BudgetLedgerPort(ABC):
    """
    Port for persistent rate-limit and quota management.
    """

    @abstractmethod
    async def acquire_permit(
        self,
        provider: str,
        cost: int = 1,
    ) -> bool:
        """Atomically check and increment quota permit. Returns True if allowed."""
        pass

    @abstractmethod
    async def get_usage(self, provider: str) -> dict[str, Any]:
        """Retrieve current usage and limits for a provider."""
        pass

