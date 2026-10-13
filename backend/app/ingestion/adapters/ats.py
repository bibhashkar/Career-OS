"""
Tier-1 ATS client adapters for Greenhouse, Lever, and Ashby public APIs.

All adapters:
- Connect directly to official, unauthenticated public endpoints.
- Require zero API keys.
- Parse structured responses into normalized DiscoveredJobDTO objects.
- Strip HTML tags safely server-side to prevent stored XSS.
- Integrate LocationNormalizer and VisaSponsorshipParser.
"""

import html
import logging
import re
from datetime import UTC, datetime

import httpx

from app.core.http import DEFAULT_TIMEOUT
from app.ingestion.models import (
    ATSProviderEnum,
    DataOrigin,
    DiscoveredJobDTO,
    RemoteScope,
    SourceConfidence,
    WorkplaceType,
)
from app.ingestion.ports.provider import ATSAdapterPort
from app.ingestion.security import sanitize_text
from app.ingestion.taxonomy import LocationNormalizer, VisaSponsorshipParser

logger = logging.getLogger("career_os.ingestion.adapters.ats")

# Regex to safely strip HTML tags from raw descriptions
HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html_to_text(raw_html: str) -> str:
    """Safely decode HTML entities and strip HTML markup into clean text."""
    if not raw_html:
        return ""
    unescaped = html.unescape(raw_html)
    with_newlines = re.sub(r"<\s*(?:br|p|div|li)[^>]*>", "\n", unescaped, flags=re.I)
    stripped = HTML_TAG_RE.sub(" ", with_newlines)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", stripped)
    return sanitize_text(cleaned)


class GreenhouseAdapter(ATSAdapterPort):
    """
    Adapter for Greenhouse Job Board API.
    Docs: https://developers.greenhouse.io/job-board.html
    Public endpoint: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
    """

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    @property
    def provider(self) -> ATSProviderEnum:
        return ATSProviderEnum.GREENHOUSE

    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        url = f"{self.BASE_URL}/{slug}/jobs?content=true"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                logger.warning("Greenhouse board '%s' not found (404)", slug)
                return []
            resp.raise_for_status()
            data = resp.json()

        jobs: list[DiscoveredJobDTO] = []
        for item in data.get("jobs", []):
            job_id = str(item.get("id"))
            title = sanitize_text(item.get("title", ""))
            location = item.get("location", {}).get("name", "Remote") or "Remote"
            apply_url = (
                item.get("absolute_url")
                or f"https://boards.greenhouse.io/{slug}/jobs/{job_id}"
            )
            raw_content = item.get("content", "")
            description = _clean_html_to_text(raw_content)

            posted_at: datetime | None = None
            if item.get("updated_at"):
                try:
                    posted_at = datetime.fromisoformat(
                        item["updated_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            loc = LocationNormalizer.normalize(location)
            visa = VisaSponsorshipParser.parse(description)

            jobs.append(
                DiscoveredJobDTO(
                    ats_provider="greenhouse",
                    ats_board_slug=slug,
                    source_job_id=job_id,
                    title=title,
                    company_name=slug.capitalize(),
                    apply_url=apply_url,
                    url=apply_url,
                    raw_location=loc.raw_location,
                    city=loc.city,
                    state_province=loc.state_province,
                    state_province_code=loc.state_province_code,
                    country=loc.country,
                    country_code=loc.country_code,
                    primary_region=loc.primary_region,
                    workplace_type=WorkplaceType(loc.workplace_type),
                    remote_scope=RemoteScope(loc.remote_scope),
                    raw_description=description or title,
                    visa_sponsorship=visa.status,
                    visa_notes=visa.notes,
                    visa_types=visa.visa_types,
                    posted_at=posted_at,
                    data_origin=DataOrigin.LIVE,
                    source_confidence=SourceConfidence.HIGH,
                    raw_metadata={"greenhouse_id": job_id},
                )
            )
        return jobs

    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        url = f"{self.BASE_URL}/{slug}/jobs/{job_id}"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            item = resp.json()

        title = sanitize_text(item.get("title", ""))
        location = item.get("location", {}).get("name", "Remote") or "Remote"
        apply_url = (
            item.get("absolute_url")
            or f"https://boards.greenhouse.io/{slug}/jobs/{job_id}"
        )
        description = _clean_html_to_text(item.get("content", ""))
        loc = LocationNormalizer.normalize(location)
        visa = VisaSponsorshipParser.parse(description)

        return DiscoveredJobDTO(
            ats_provider="greenhouse",
            ats_board_slug=slug,
            source_job_id=job_id,
            title=title,
            company_name=slug.capitalize(),
            apply_url=apply_url,
            url=apply_url,
            raw_location=loc.raw_location,
            city=loc.city,
            state_province=loc.state_province,
            state_province_code=loc.state_province_code,
            country=loc.country,
            country_code=loc.country_code,
            primary_region=loc.primary_region,
            workplace_type=WorkplaceType(loc.workplace_type),
            remote_scope=RemoteScope(loc.remote_scope),
            raw_description=description or title,
            visa_sponsorship=visa.status,
            visa_notes=visa.notes,
            visa_types=visa.visa_types,
            posted_at=datetime.now(UTC),
            data_origin=DataOrigin.LIVE,
            source_confidence=SourceConfidence.HIGH,
            raw_metadata={"greenhouse_id": job_id},
        )


class LeverAdapter(ATSAdapterPort):
    """
    Adapter for Lever Postings API.
    Docs: https://github.com/lever/postings-api
    Public endpoint: https://api.lever.co/v0/postings/{slug}?mode=json
    """

    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    @property
    def provider(self) -> ATSProviderEnum:
        return ATSProviderEnum.LEVER

    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        url = f"{self.BASE_URL}/{slug}?mode=json"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                logger.warning("Lever board '%s' not found (404)", slug)
                return []
            resp.raise_for_status()
            data = resp.json()

        jobs: list[DiscoveredJobDTO] = []
        for item in data:
            job_id = str(item.get("id"))
            title = sanitize_text(item.get("text", ""))
            categories = item.get("categories", {})
            location = categories.get("location", "Remote") or "Remote"
            apply_url = (
                item.get("applyUrl")
                or item.get("hostedUrl")
                or f"https://jobs.lever.co/{slug}/{job_id}"
            )
            description = sanitize_text(
                item.get("descriptionPlain", "") or item.get("description", "")
            )

            posted_at: datetime | None = None
            if item.get("createdAt"):
                try:
                    posted_at = datetime.fromtimestamp(item["createdAt"] / 1000, tz=UTC)
                except (ValueError, OSError):
                    pass

            loc = LocationNormalizer.normalize(location)
            visa = VisaSponsorshipParser.parse(description)

            jobs.append(
                DiscoveredJobDTO(
                    ats_provider="lever",
                    ats_board_slug=slug,
                    source_job_id=job_id,
                    title=title,
                    company_name=slug.capitalize(),
                    apply_url=apply_url,
                    url=apply_url,
                    raw_location=loc.raw_location,
                    city=loc.city,
                    state_province=loc.state_province,
                    state_province_code=loc.state_province_code,
                    country=loc.country,
                    country_code=loc.country_code,
                    primary_region=loc.primary_region,
                    workplace_type=WorkplaceType(loc.workplace_type),
                    remote_scope=RemoteScope(loc.remote_scope),
                    raw_description=description or title,
                    visa_sponsorship=visa.status,
                    visa_notes=visa.notes,
                    visa_types=visa.visa_types,
                    posted_at=posted_at,
                    data_origin=DataOrigin.LIVE,
                    source_confidence=SourceConfidence.HIGH,
                    raw_metadata={"lever_id": job_id},
                )
            )
        return jobs

    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        url = f"{self.BASE_URL}/{slug}/{job_id}"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            item = resp.json()

        title = sanitize_text(item.get("text", ""))
        categories = item.get("categories", {})
        location = categories.get("location", "Remote") or "Remote"
        apply_url = (
            item.get("applyUrl")
            or item.get("hostedUrl")
            or f"https://jobs.lever.co/{slug}/{job_id}"
        )
        description = sanitize_text(
            item.get("descriptionPlain", "") or item.get("description", "")
        )
        loc = LocationNormalizer.normalize(location)
        visa = VisaSponsorshipParser.parse(description)

        return DiscoveredJobDTO(
            ats_provider="lever",
            ats_board_slug=slug,
            source_job_id=job_id,
            title=title,
            company_name=slug.capitalize(),
            apply_url=apply_url,
            url=apply_url,
            raw_location=loc.raw_location,
            city=loc.city,
            state_province=loc.state_province,
            state_province_code=loc.state_province_code,
            country=loc.country,
            country_code=loc.country_code,
            primary_region=loc.primary_region,
            workplace_type=WorkplaceType(loc.workplace_type),
            remote_scope=RemoteScope(loc.remote_scope),
            raw_description=description or title,
            visa_sponsorship=visa.status,
            visa_notes=visa.notes,
            visa_types=visa.visa_types,
            posted_at=datetime.now(UTC),
            data_origin=DataOrigin.LIVE,
            source_confidence=SourceConfidence.HIGH,
            raw_metadata={"lever_id": job_id},
        )


class AshbyAdapter(ATSAdapterPort):
    """
    Adapter for Ashby Job Postings API.
    Public endpoint: https://api.ashbyhq.com/posting-api/job-board/{slug}
    """

    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    @property
    def provider(self) -> ATSProviderEnum:
        return ATSProviderEnum.ASHBY

    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        url = f"{self.BASE_URL}/{slug}"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                logger.warning("Ashby board '%s' not found (404)", slug)
                return []
            resp.raise_for_status()
            data = resp.json()

        jobs_data = (
            data.get("jobs", [])
            or data.get("data", {}).get("jobPostings", [])
            or data.get("jobPostings", [])
        )
        jobs: list[DiscoveredJobDTO] = []

        for item in jobs_data:
            job_id = str(item.get("id"))
            title = sanitize_text(item.get("title", ""))
            location = item.get("location") or item.get("locationName") or "Remote"
            apply_url = (
                item.get("applyUrl")
                or item.get("jobUrl")
                or f"https://jobs.ashbyhq.com/{slug}/{job_id}"
            )
            raw_desc = item.get("descriptionPlain") or item.get("descriptionHtml") or ""
            description = (
                _clean_html_to_text(raw_desc)
                if "<" in raw_desc
                else sanitize_text(raw_desc)
            )

            posted_at: datetime | None = None
            date_str = item.get("publishedAt") or item.get("publishedDate")
            if date_str:
                try:
                    posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            loc = LocationNormalizer.normalize(location)
            if item.get("isRemote"):
                loc.workplace_type = "remote"
                if loc.remote_scope == "none":
                    loc.remote_scope = "country_wide"
            visa = VisaSponsorshipParser.parse(description)

            jobs.append(
                DiscoveredJobDTO(
                    ats_provider="ashby",
                    ats_board_slug=slug,
                    source_job_id=job_id,
                    title=title,
                    company_name=slug.capitalize(),
                    apply_url=apply_url,
                    url=apply_url,
                    raw_location=loc.raw_location,
                    city=loc.city,
                    state_province=loc.state_province,
                    state_province_code=loc.state_province_code,
                    country=loc.country,
                    country_code=loc.country_code,
                    primary_region=loc.primary_region,
                    workplace_type=WorkplaceType(loc.workplace_type),
                    remote_scope=RemoteScope(loc.remote_scope),
                    raw_description=description or title,
                    visa_sponsorship=visa.status,
                    visa_notes=visa.notes,
                    visa_types=visa.visa_types,
                    posted_at=posted_at,
                    data_origin=DataOrigin.LIVE,
                    source_confidence=SourceConfidence.HIGH,
                    raw_metadata={"ashby_id": job_id},
                )
            )
        return jobs

    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        jobs = await self.fetch_board_jobs(slug)
        for job in jobs:
            if job.source_job_id == job_id:
                return job
        return None
