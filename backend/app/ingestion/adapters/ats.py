"""
Tier-1 ATS client adapters for Greenhouse, Lever, and Ashby public APIs.

All adapters:
- Connect directly to official, unauthenticated public endpoints.
- Require zero API keys.
- Parse structured responses into normalized DiscoveredJobDTO objects.
- Strip HTML tags safely server-side to prevent stored XSS.
- Integrate LocationNormalizer and VisaSponsorshipParser.
"""

import asyncio
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


class WorkableAdapter(ATSAdapterPort):
    """
    Adapter for Workable Job Board API.
    Public list endpoint: POST https://apply.workable.com/api/v3/accounts/{slug}/jobs
    Public detail endpoint: GET https://apply.workable.com/api/v3/accounts/{slug}/jobs/{shortcode}
    """

    BASE_URL = "https://apply.workable.com/api/v3/accounts"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    @property
    def provider(self) -> ATSProviderEnum:
        return ATSProviderEnum.WORKABLE

    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        url = f"{self.BASE_URL}/{slug}/jobs"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                resp = await client.post(
                    url,
                    json={"query": ""},
                    headers={"User-Agent": "Career-OS Ingestion/2.0"},
                )
            except Exception as exc:
                logger.error("Workable network error for board '%s': %s", slug, exc)
                return []

            if resp.status_code == 404:
                logger.warning("Workable board '%s' not found (404)", slug)
                return []
            if resp.status_code != 200:
                logger.error(
                    "Workable board '%s' returned status %d", slug, resp.status_code
                )
                return []

            data = resp.json()
            raw_jobs = data.get("results", [])
            if not raw_jobs:
                return []

            sem = asyncio.Semaphore(5)

            async def _fetch_detail(item: dict) -> DiscoveredJobDTO | None:
                shortcode = item.get("shortcode") or item.get("id")
                if not shortcode:
                    return None

                title = sanitize_text(item.get("title", ""))
                if not title:
                    return None

                city = item.get("city")
                country = item.get("country")
                country_code = item.get("countryCode")
                state = item.get("state")
                raw_loc = (
                    ", ".join(
                        [p for p in [city, state, country] if p and str(p).strip()]
                    )
                    or "Remote"
                )

                loc = LocationNormalizer.normalize(raw_loc)
                if country_code:
                    loc.country_code = country_code.upper()

                workplace = (item.get("workplace") or "").lower()
                if workplace == "remote":
                    loc.workplace_type = "remote"
                    if loc.remote_scope == "none":
                        loc.remote_scope = "country_wide"
                elif workplace == "hybrid":
                    loc.workplace_type = "hybrid"
                elif workplace == "on_site":
                    loc.workplace_type = "on_site"

                # Fetch rich description from detail endpoint
                detail_url = f"{self.BASE_URL}/{slug}/jobs/{shortcode}"
                description = title
                async with sem:
                    try:
                        det_resp = await client.get(
                            detail_url,
                            headers={"User-Agent": "Career-OS Ingestion/2.0"},
                        )
                        if det_resp.status_code == 200:
                            det_data = det_resp.json()
                            raw_desc = det_data.get("description", "")
                            raw_reqs = det_data.get("requirements", "")
                            combined = f"{raw_desc}\n\n{raw_reqs}".strip()
                            if combined:
                                description = _clean_html_to_text(combined)
                    except Exception as e:
                        logger.debug(
                            "Workable detail fetch failed for %s:%s: %s",
                            slug,
                            shortcode,
                            e,
                        )

                visa = VisaSponsorshipParser.parse(description)
                apply_url = (
                    item.get("applicationUrl")
                    or item.get("url")
                    or f"https://apply.workable.com/{slug}/j/{shortcode}/"
                )

                posted_at: datetime | None = None
                date_str = item.get("published")
                if date_str:
                    try:
                        posted_at = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                return DiscoveredJobDTO(
                    ats_provider="workable",
                    ats_board_slug=slug,
                    source_job_id=str(shortcode),
                    title=title,
                    company_name=slug.capitalize(),
                    apply_url=apply_url,
                    url=item.get("url") or apply_url,
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
                    raw_metadata={"workable_shortcode": shortcode},
                )

            tasks = [_fetch_detail(item) for item in raw_jobs]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]

    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        url = f"{self.BASE_URL}/{slug}/jobs/{job_id}"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Career-OS Ingestion/2.0"},
                )
                if resp.status_code != 200:
                    return None
                data = resp.json()
                title = sanitize_text(data.get("title", ""))
                if not title:
                    return None

                raw_desc = data.get("description", "")
                raw_reqs = data.get("requirements", "")
                description = (
                    _clean_html_to_text(f"{raw_desc}\n\n{raw_reqs}".strip()) or title
                )

                city = data.get("city")
                country = data.get("country")
                country_code = data.get("countryCode")
                state = data.get("state")
                raw_loc = (
                    ", ".join(
                        [p for p in [city, state, country] if p and str(p).strip()]
                    )
                    or "Remote"
                )

                loc = LocationNormalizer.normalize(raw_loc)
                if country_code:
                    loc.country_code = country_code.upper()

                workplace = (data.get("workplace") or "").lower()
                if workplace == "remote":
                    loc.workplace_type = "remote"
                    if loc.remote_scope == "none":
                        loc.remote_scope = "country_wide"
                elif workplace == "hybrid":
                    loc.workplace_type = "hybrid"
                elif workplace == "on_site":
                    loc.workplace_type = "on_site"

                visa = VisaSponsorshipParser.parse(description)
                apply_url = (
                    data.get("applicationUrl")
                    or data.get("url")
                    or f"https://apply.workable.com/{slug}/j/{job_id}/"
                )

                posted_at: datetime | None = None
                date_str = data.get("published")
                if date_str:
                    try:
                        posted_at = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                return DiscoveredJobDTO(
                    ats_provider="workable",
                    ats_board_slug=slug,
                    source_job_id=str(job_id),
                    title=title,
                    company_name=slug.capitalize(),
                    apply_url=apply_url,
                    url=data.get("url") or apply_url,
                    raw_location=loc.raw_location,
                    city=loc.city,
                    state_province=loc.state_province,
                    state_province_code=loc.state_province_code,
                    country=loc.country,
                    country_code=loc.country_code,
                    primary_region=loc.primary_region,
                    workplace_type=WorkplaceType(loc.workplace_type),
                    remote_scope=RemoteScope(loc.remote_scope),
                    raw_description=description,
                    visa_sponsorship=visa.status,
                    visa_notes=visa.notes,
                    visa_types=visa.visa_types,
                    posted_at=posted_at,
                    data_origin=DataOrigin.LIVE,
                    source_confidence=SourceConfidence.HIGH,
                    raw_metadata={"workable_shortcode": job_id},
                )
            except Exception as exc:
                logger.error("Workable detail error for %s:%s: %s", slug, job_id, exc)
                return None


class SmartRecruitersAdapter(ATSAdapterPort):
    """
    Adapter for SmartRecruiters Job Board API.
    Public list endpoint: GET https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100
    Public detail endpoint: GET https://api.smartrecruiters.com/v1/companies/{slug}/postings/{id}
    """

    BASE_URL = "https://api.smartrecruiters.com/v1/companies"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    @property
    def provider(self) -> ATSProviderEnum:
        return ATSProviderEnum.SMARTRECRUITERS

    async def fetch_board_jobs(self, slug: str) -> list[DiscoveredJobDTO]:
        url = f"{self.BASE_URL}/{slug}/postings?limit=100"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Career-OS Ingestion/2.0"},
                )
            except Exception as exc:
                logger.error(
                    "SmartRecruiters network error for board '%s': %s", slug, exc
                )
                return []

            if resp.status_code == 404:
                logger.warning("SmartRecruiters board '%s' not found (404)", slug)
                return []
            if resp.status_code != 200:
                logger.error(
                    "SmartRecruiters board '%s' returned status %d",
                    slug,
                    resp.status_code,
                )
                return []

            data = resp.json()
            raw_jobs = data.get("content", [])
            if not raw_jobs:
                return []

            sem = asyncio.Semaphore(5)

            async def _fetch_detail(item: dict) -> DiscoveredJobDTO | None:
                job_id = str(item.get("id", ""))
                title = sanitize_text(item.get("name", ""))
                if not job_id or not title:
                    return None

                loc_data = item.get("location") or {}
                city = loc_data.get("city")
                country_code = loc_data.get("country")
                region_name = loc_data.get("region")
                raw_loc = (
                    loc_data.get("fullLocation")
                    or ", ".join(
                        [
                            p
                            for p in [city, region_name, country_code]
                            if p and str(p).strip()
                        ]
                    )
                    or "Remote"
                )

                loc = LocationNormalizer.normalize(raw_loc)
                if country_code:
                    loc.country_code = country_code.upper()

                if loc_data.get("remote"):
                    loc.workplace_type = "remote"
                    if loc.remote_scope == "none":
                        loc.remote_scope = "country_wide"
                elif loc_data.get("hybrid"):
                    loc.workplace_type = "hybrid"

                company_name = (item.get("company") or {}).get(
                    "name"
                ) or slug.capitalize()

                # Fetch rich description from detail endpoint
                detail_url = f"{self.BASE_URL}/{slug}/postings/{job_id}"
                description = title
                apply_url = f"https://jobs.smartrecruiters.com/{slug}/{job_id}"

                async with sem:
                    try:
                        det_resp = await client.get(
                            detail_url,
                            headers={"User-Agent": "Career-OS Ingestion/2.0"},
                        )
                        if det_resp.status_code == 200:
                            det_data = det_resp.json()
                            apply_url = (
                                det_data.get("applyUrl")
                                or det_data.get("postingUrl")
                                or apply_url
                            )
                            job_ad = det_data.get("jobAd") or {}
                            sections = job_ad.get("sections") or {}
                            job_desc = (sections.get("jobDescription") or {}).get(
                                "text", ""
                            )
                            quals = (sections.get("qualifications") or {}).get(
                                "text", ""
                            )
                            combined = f"{job_desc}\n\n{quals}".strip()
                            if combined:
                                description = _clean_html_to_text(combined)
                    except Exception as e:
                        logger.debug(
                            "SmartRecruiters detail fetch failed for %s:%s: %s",
                            slug,
                            job_id,
                            e,
                        )

                visa = VisaSponsorshipParser.parse(description)

                posted_at: datetime | None = None
                date_str = item.get("releasedDate")
                if date_str:
                    try:
                        posted_at = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                return DiscoveredJobDTO(
                    ats_provider="smartrecruiters",
                    ats_board_slug=slug,
                    source_job_id=job_id,
                    title=title,
                    company_name=company_name,
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
                    raw_metadata={"smartrecruiters_id": job_id},
                )

            tasks = [_fetch_detail(item) for item in raw_jobs]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]

    async def fetch_job_detail(self, slug: str, job_id: str) -> DiscoveredJobDTO | None:
        url = f"{self.BASE_URL}/{slug}/postings/{job_id}"
        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            try:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Career-OS Ingestion/2.0"},
                )
                if resp.status_code != 200:
                    return None
                det_data = resp.json()
                title = sanitize_text(det_data.get("name", ""))
                if not title:
                    return None

                job_ad = det_data.get("jobAd") or {}
                sections = job_ad.get("sections") or {}
                job_desc = (sections.get("jobDescription") or {}).get("text", "")
                quals = (sections.get("qualifications") or {}).get("text", "")
                description = (
                    _clean_html_to_text(f"{job_desc}\n\n{quals}".strip()) or title
                )

                loc_data = det_data.get("location") or {}
                city = loc_data.get("city")
                country_code = loc_data.get("country")
                region_name = loc_data.get("region")
                raw_loc = (
                    loc_data.get("fullLocation")
                    or ", ".join(
                        [
                            p
                            for p in [city, region_name, country_code]
                            if p and str(p).strip()
                        ]
                    )
                    or "Remote"
                )

                loc = LocationNormalizer.normalize(raw_loc)
                if country_code:
                    loc.country_code = country_code.upper()

                if loc_data.get("remote"):
                    loc.workplace_type = "remote"
                    if loc.remote_scope == "none":
                        loc.remote_scope = "country_wide"
                elif loc_data.get("hybrid"):
                    loc.workplace_type = "hybrid"

                company_name = (det_data.get("company") or {}).get(
                    "name"
                ) or slug.capitalize()
                apply_url = (
                    det_data.get("applyUrl")
                    or det_data.get("postingUrl")
                    or f"https://jobs.smartrecruiters.com/{slug}/{job_id}"
                )

                visa = VisaSponsorshipParser.parse(description)

                posted_at: datetime | None = None
                date_str = det_data.get("releasedDate")
                if date_str:
                    try:
                        posted_at = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

                return DiscoveredJobDTO(
                    ats_provider="smartrecruiters",
                    ats_board_slug=slug,
                    source_job_id=job_id,
                    title=title,
                    company_name=company_name,
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
                    raw_description=description,
                    visa_sponsorship=visa.status,
                    visa_notes=visa.notes,
                    visa_types=visa.visa_types,
                    posted_at=posted_at,
                    data_origin=DataOrigin.LIVE,
                    source_confidence=SourceConfidence.HIGH,
                    raw_metadata={"smartrecruiters_id": job_id},
                )
            except Exception as exc:
                logger.error(
                    "SmartRecruiters detail error for %s:%s: %s", slug, job_id, exc
                )
                return None
