"""
Board synchronization service and deduplication engine.

Calculates cross-source deduplication fingerprints:
  fingerprint = hash(normalized company, normalized title, normalized location region)
and performs atomic upserts, tracking first_seen_at, last_seen_at, and soft-closing
jobs absent from consecutive board syncs.
"""

import hashlib
import logging
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.adapters.ats import (
    AshbyAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    SmartRecruitersAdapter,
    WorkableAdapter,
)
from app.ingestion.deterministic_extractor import (
    classify_industry_vertical,
    extract_deterministic_requirements,
    extract_domain_strictness,
)
from app.ingestion.models import (
    ATSProviderEnum,
    DiscoveredJobDTO,
    ListingStatus,
)
from app.ingestion.ports.provider import ATSAdapterPort
from app.models.ingestion import ATSBoard, IngestionRun
from app.models.job_listing import JobListing

logger = logging.getLogger("career_os.ingestion.service")


def compute_dedupe_fingerprint(company: str, title: str, location: str) -> str:
    """
    Compute cross-source dedupe fingerprint:
    hash(normalized company, normalized title, normalized location region).
    """
    norm_company = re.sub(r"[^a-z0-9]", "", company.lower())
    norm_title = re.sub(r"[^a-z0-9]", "", title.lower())
    norm_loc = re.sub(r"[^a-z0-9]", "", location.lower())
    raw = f"{norm_company}:{norm_title}:{norm_loc}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def compute_content_hash(description: str) -> str:
    """Compute sha256 hash of job description text for change tracking."""
    return hashlib.sha256(description.encode("utf-8")).hexdigest()[:32]


def normalize_job_title(title: str) -> str:
    """Normalize job title by lowercasing and stripping trailing geographic markers."""
    t = title.lower().strip()
    t = re.sub(
        r"\s*-\s*(nyc|new york|sf|san francisco|toronto|boston|austin|seattle|chicago|london|berlin|munich|madrid|dublin|bengaluru|singapore|sydney|remote)\b",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\s*\((remote\s+[a-z]+|remote|us|usa|emea|apac|latam|canada)\)\s*$",
        "",
        t,
        flags=re.IGNORECASE,
    )
    return re.sub(r"[^a-z0-9]", "", t)


def compute_canonical_fingerprint(company: str, title: str) -> str:
    """Compute canonical requisition fingerprint invariant to geographic variants."""
    norm_company = re.sub(r"[^a-z0-9]", "", company.lower())
    norm_title = normalize_job_title(title)
    raw = f"{norm_company}:{norm_title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class BoardSyncService:
    """
    Synchronizes jobs from an ATS board into the local job_listing store.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._adapters: dict[str, ATSAdapterPort] = {
            ATSProviderEnum.GREENHOUSE.value: GreenhouseAdapter(),
            ATSProviderEnum.LEVER.value: LeverAdapter(),
            ATSProviderEnum.ASHBY.value: AshbyAdapter(),
            ATSProviderEnum.WORKABLE.value: WorkableAdapter(),
            ATSProviderEnum.SMARTRECRUITERS.value: SmartRecruitersAdapter(),
        }

    def register_adapter(self, provider: str, adapter: ATSAdapterPort) -> None:
        """Register custom or mocked ATS adapter."""
        key = provider.value if hasattr(provider, "value") else str(provider).lower()
        self._adapters[key] = adapter

    async def get_or_create_board(self, provider_str: str, slug: str) -> ATSBoard:
        """Ensure an ATSBoard record exists in the database for relational safety."""
        stmt = select(ATSBoard).where(
            ATSBoard.provider == provider_str.lower(),
            ATSBoard.slug == slug.lower(),
        )
        board = (await self.session.execute(stmt)).scalar_one_or_none()
        if not board:
            board = ATSBoard(
                provider=provider_str.lower(),
                slug=slug.lower(),
                company_name=slug.capitalize(),
                industry="enterprise_saas",
                is_active=True,
            )
            self.session.add(board)
            await self.session.flush()
        return board

    async def sync_board(self, provider_str: str, slug: str) -> IngestionRun:
        """
        Execute full board sync:
        1. Ensure ATSBoard entity exists in database.
        2. Fetch open jobs via provider adapter.
        3. Upsert into job_listing table.
        4. Detect missing jobs and soft-close them.
        5. Log metrics to ingestion_run table.
        """
        start_time = datetime.now(UTC)
        prov_key = provider_str.lower()
        slug_key = slug.lower()

        adapter = self._adapters.get(prov_key)
        if not adapter:
            raise ValueError(f"No adapter registered for ATS provider '{provider_str}'")

        board = await self.get_or_create_board(prov_key, slug_key)

        run = IngestionRun(
            ats_board_id=board.id,
            ats_provider=prov_key,
            board_slug=slug_key,
            status="running",
            fetched_count=0,
            new_count=0,
            updated_count=0,
            closed_count=0,
            rejected_count=0,
            duration_ms=0,
        )
        self.session.add(run)
        await self.session.flush()

        try:
            discovered_jobs = await adapter.fetch_board_jobs(slug_key)
            run.fetched_count = len(discovered_jobs)

            current_source_ids = {j.source_job_id for j in discovered_jobs}

            # Upsert discovered jobs
            for dto in discovered_jobs:
                is_new = await self._upsert_job(dto, board)
                if is_new:
                    run.new_count += 1
                else:
                    run.updated_count += 1

            # Detect closed jobs:
            # currently active jobs for this board absent from the latest response
            stmt = select(JobListing).where(
                JobListing.ats_board_id == board.id,
                JobListing.status == ListingStatus.ACTIVE,
            )
            existing_active = (await self.session.execute(stmt)).scalars().all()

            for active_job in existing_active:
                if active_job.source_job_id not in current_source_ids:
                    active_job.status = ListingStatus.CLOSED
                    active_job.last_seen_at = datetime.now(UTC)
                    run.closed_count += 1

            # Update ATSBoard sync metadata
            board.last_synced_at = datetime.now(UTC)
            board.consecutive_failures = 0

            run.status = "success"

        except Exception as e:
            logger.error(
                "Board sync failed for %s:%s: %s", prov_key, slug_key, e, exc_info=True
            )
            run.status = "failed"
            run.error_message = str(e)
            board.consecutive_failures += 1

        end_time = datetime.now(UTC)
        run.duration_ms = int((end_time - start_time).total_seconds() * 1000)
        await self.session.flush()
        return run

    async def _upsert_job(self, dto: DiscoveredJobDTO, board: ATSBoard) -> bool:
        """
        Upsert a discovered job listing with foreign key relational integrity.
        Returns True if newly created, False if updated.
        """
        comp_name = board.company_name or dto.company_name
        fingerprint = compute_dedupe_fingerprint(comp_name, dto.title, dto.raw_location)
        canonical_fp = compute_canonical_fingerprint(comp_name, dto.title)
        content_hash = compute_content_hash(dto.raw_description)

        # 1. Exact ATS identity check
        stmt = select(JobListing).where(
            JobListing.ats_provider == dto.ats_provider,
            JobListing.ats_board_slug == dto.ats_board_slug,
            JobListing.source_job_id == dto.source_job_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        # 2. Cross-source exact fingerprint check (same company + title + location)
        if existing is None and fingerprint:
            stmt_fp = select(JobListing).where(JobListing.fingerprint == fingerprint)
            existing = (await self.session.execute(stmt_fp)).scalar_one_or_none()

        # 3. Canonical requisition check (same company + normalized title for multi-location postings)
        if existing is None and canonical_fp:
            stmt_canon = select(JobListing).where(
                JobListing.canonical_fingerprint == canonical_fp,
                JobListing.status == ListingStatus.ACTIVE,
            )
            existing = (await self.session.execute(stmt_canon)).scalars().first()

        now = datetime.now(UTC)

        modality = (
            dto.workplace_type.value
            if hasattr(dto.workplace_type, "value")
            else str(dto.workplace_type)
        )
        scope = (
            dto.remote_scope.value
            if hasattr(dto.remote_scope, "value")
            else str(dto.remote_scope)
        )
        job_industry = board.industry or dto.industry or "enterprise_saas"
        vertical = classify_industry_vertical(
            dto.title, dto.raw_description, board.company_name or dto.company_name
        )
        strictness = extract_domain_strictness(dto.title, dto.raw_description, vertical)
        reqs = extract_deterministic_requirements(
            dto.title, dto.raw_description, board.company_name or dto.company_name
        )
        ats_reqs_dict = reqs.model_dump()

        if existing is None:
            initial_posting = {
                "location": dto.raw_location,
                "city": dto.city,
                "state_province": dto.state_province,
                "state_code": dto.state_province_code,
                "country": dto.country,
                "country_code": dto.country_code,
                "salary_range": dto.salary_range,
                "source_job_id": dto.source_job_id,
                "apply_url": dto.apply_url,
                "is_primary": True,
            }
            new_job = JobListing(
                ats_board_id=board.id,
                ats_provider=dto.ats_provider,
                ats_board_slug=dto.ats_board_slug,
                source_job_id=dto.source_job_id,
                industry=job_industry,
                industry_vertical=vertical,
                domain_strictness=strictness,
                company_dossier_id=board.company_dossier_id,
                title=dto.title,
                company_name=board.company_name or dto.company_name,
                apply_url=dto.apply_url,
                url=dto.apply_url,
                raw_location=dto.raw_location,
                city=dto.city,
                state_province=dto.state_province,
                state_province_code=dto.state_province_code,
                country=dto.country,
                country_code=dto.country_code,
                primary_region=dto.primary_region or board.primary_region,
                workplace_type=modality,
                remote_scope=scope,
                salary_range=dto.salary_range,
                raw_description=dto.raw_description,
                visa_sponsorship=dto.visa_sponsorship
                or str(reqs.visa_sponsorship.value),
                visa_notes=dto.visa_notes,
                visa_types=dto.visa_types,
                posted_at=dto.posted_at,
                first_seen_at=now,
                last_seen_at=now,
                last_fetched_at=now,
                fingerprint=fingerprint,
                canonical_fingerprint=canonical_fp,
                location_postings=[initial_posting],
                content_hash=content_hash,
                status=ListingStatus.ACTIVE,
                data_origin=str(dto.data_origin),
                source_confidence=str(dto.source_confidence),
                ats_requirements=ats_reqs_dict,
                verification={},
            )
            self.session.add(new_job)
            return True

        # Existing job: consolidate locations, update timestamps, and reactivate
        existing.last_seen_at = now
        existing.last_fetched_at = now
        existing.status = ListingStatus.ACTIVE
        if not existing.canonical_fingerprint:
            existing.canonical_fingerprint = canonical_fp

        loc_entry = {
            "location": dto.raw_location,
            "city": dto.city,
            "state_province": dto.state_province,
            "state_code": dto.state_province_code,
            "country": dto.country,
            "country_code": dto.country_code,
            "salary_range": dto.salary_range,
            "source_job_id": dto.source_job_id,
            "apply_url": dto.apply_url,
            "is_primary": False,
        }
        postings = list(existing.location_postings or [])
        if not any(
            p.get("source_job_id") == dto.source_job_id
            or (
                p.get("location") == dto.raw_location
                and p.get("apply_url") == dto.apply_url
            )
            for p in postings
        ):
            postings.append(loc_entry)
            existing.location_postings = postings

        # Consolidate raw_location if new location is distinct
        if (
            dto.raw_location
            and dto.raw_location.lower() not in (existing.raw_location or "").lower()
        ):
            if existing.raw_location:
                existing.raw_location = f"{existing.raw_location}, {dto.raw_location}"
            else:
                existing.raw_location = dto.raw_location
        if not existing.apply_url:
            existing.apply_url = dto.apply_url
        existing.status = ListingStatus.ACTIVE
        existing.workplace_type = modality
        existing.remote_scope = scope
        if dto.city:
            existing.city = dto.city
        if dto.state_province_code:
            existing.state_province_code = dto.state_province_code
        if dto.country_code:
            existing.country_code = dto.country_code
        if dto.visa_sponsorship:
            existing.visa_sponsorship = dto.visa_sponsorship
            existing.visa_notes = dto.visa_notes
            existing.visa_types = dto.visa_types
        elif not existing.visa_sponsorship and reqs.visa_sponsorship.value != "unknown":
            existing.visa_sponsorship = str(reqs.visa_sponsorship.value)
        if not existing.industry_vertical:
            existing.industry_vertical = vertical
            existing.domain_strictness = strictness
        if not existing.ats_requirements or existing.ats_requirements == {}:
            existing.ats_requirements = ats_reqs_dict

        if existing.content_hash != content_hash:
            existing.raw_description = dto.raw_description
            existing.content_hash = content_hash
            existing.title = dto.title
            existing.ats_requirements = ats_reqs_dict

        return False
