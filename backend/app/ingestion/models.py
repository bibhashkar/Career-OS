"""
Pure domain data transfer objects (DTOs) and enums for data ingestion.
"""

from datetime import datetime
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
    """Tri-state visa sponsorship policy indicator."""

    YES = "yes"
    NO = "no"
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


class ATSProvider(StrEnum):
    """Supported Applicant Tracking System providers."""

    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    SMARTRECRUITERS = "smartrecruiters"
    CUSTOM = "custom"


class IngestionTaskType(StrEnum):
    """Supported asynchronous ingestion queue task types."""

    SYNC_BOARD = "sync_board"
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

    source: str
    source_job_id: str
    title: str
    company_name: str
    apply_url: str
    location: str = "Remote"
    salary_range: str | None = None
    raw_description: str
    remote_type: str | None = None
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
    extraction_version: str = "v1"
    confidence_score: float = 1.0
    needs_review: bool = False
    evidence: dict[str, list[str]] = Field(default_factory=dict)


class FieldProvenanceDTO(BaseModel):
    """Provenance audit trail for a single company dossier field."""

    method: str  # "verified" | "inferred" | "unknown"
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


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
