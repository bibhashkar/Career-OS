"""
Pure domain data transfer objects (DTOs) and enums for data ingestion.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DataOrigin(StrEnum):
    """Origin of a job listing or company dossier record."""

    LIVE = "live"
    MANUAL = "manual"
    DEMO = "demo"
    LEGACY = "legacy"
    INFERRED = "inferred"


class VisaSponsorshipStatus(StrEnum):
    """Visa sponsorship policy indicator."""

    YES = "yes"
    NO = "no"
    TRANSFER_ONLY = "transfer_only"
    OPT_CPT_ACCEPTED = "opt_cpt_accepted"
    UNKNOWN = "unknown"


class ListingStatus(StrEnum):
    """Lifecycle status of a job listing."""

    ACTIVE = "active"
    CLOSED = "closed"
    STALE = "stale"


class SourceConfidence(StrEnum):
    """Confidence tier based on information source quality."""

    HIGH = "high"  # Direct ATS API / Careers portal
    MEDIUM = "medium"  # Verified employer site / trusted feeds
    LOW = "low"  # Multi-board aggregator or scraped listings


class ATSProviderEnum(StrEnum):
    """Supported Applicant Tracking System provider codes."""

    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKABLE = "workable"
    SMARTRECRUITERS = "smartrecruiters"
    CUSTOM = "custom"


ATSProvider = ATSProviderEnum


class WorkplaceType(StrEnum):
    """Physical work modality."""

    ON_SITE = "on_site"
    HYBRID = "hybrid"
    REMOTE = "remote"


class RemoteScope(StrEnum):
    """Geographic & legal jurisdiction for remote roles."""

    NONE = "none"
    STATE_PROVINCE = "state_province"
    COUNTRY_WIDE = "country_wide"
    REGIONAL_TIMEZONE = "regional_timezone"
    WORLDWIDE_GLOBAL = "worldwide_global"


class IngestionTaskType(StrEnum):
    """Supported asynchronous ingestion queue task types."""

    SYNC_BOARD = "sync_board"
    PROBE_SLUG = "probe_slug"
    HARVEST_DIRECTORY = "harvest_directory"
    INGEST_URL = "ingest_url"
    INGEST_TEXT = "ingest_text"
    EXTRACT_REQUIREMENTS = "extract_requirements"
    REFRESH_COMPANY = "refresh_company"
    CROSS_CHECK_JOB = "cross_check_job"


class IngestionTaskStatus(StrEnum):
    """Status lifecycle of an ingestion queue task."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DiscoveredJobDTO(BaseModel):
    """DTO representing a job posting discovered from an ATS or source."""

    ats_provider: str
    ats_board_slug: str
    source_job_id: str
    title: str
    company_name: str
    apply_url: str
    url: str | None = None
    raw_location: str = "Remote"
    city: str | None = None
    state_province: str | None = None
    state_province_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    primary_region: str | None = None
    workplace_type: WorkplaceType = WorkplaceType.ON_SITE
    remote_scope: RemoteScope = RemoteScope.NONE
    salary_range: str | None = None
    raw_description: str
    industry: str | None = None
    visa_sponsorship: str | None = None
    visa_notes: str | None = None
    visa_types: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    data_origin: DataOrigin = DataOrigin.LIVE
    source_confidence: SourceConfidence = SourceConfidence.HIGH
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedRequirementsDTO(BaseModel):
    """DTO representing structured technical and visa requirements."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: int | None = None
    visa_sponsorship: VisaSponsorshipStatus = VisaSponsorshipStatus.UNKNOWN
    extraction_version: str = "v2"
    confidence_score: float = 1.0
    needs_review: bool = False
    industry_vertical: str = "general_saas"
    domain_strictness: float = 0.5
    evidence: dict[str, list[str]] = Field(default_factory=dict)


class FieldProvenanceDTO(BaseModel):
    """Provenance audit trail for a single company dossier field."""

    method: str  # "verified" | "inferred" | "unknown"
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CompanyDossierDTO(BaseModel):
    """DTO representing verified intelligence for an employer."""

    company_name: str
    canonical_name: str
    domain: str | None = None
    industry: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    recent_news: list[dict[str, Any]] = Field(default_factory=list)
    business_model: str | None = None
    culture_notes: str | None = None
    data_origin: DataOrigin = DataOrigin.LIVE
    field_provenance: dict[str, FieldProvenanceDTO] = Field(default_factory=dict)
    last_fetched_at: datetime | None = None
    next_refresh_at: datetime | None = None
