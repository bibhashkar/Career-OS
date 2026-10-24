"""
Search engine schemas, DTOs, and enumeration contracts.

Defines the Command-Facet search criteria, tokenized entity filters,
and zero-dead-end diagnostic relaxation payloads per the Career-OS
Discovery Architecture Specification (v1.0.0).
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SearchMode(StrEnum):
    """
    Search ranking mode.

    CV_GROUNDED: Ranks via P(Match) using candidate CV embeddings and skill DAG.
    UNBIASED: Raw market discovery disconnected from candidate persona.
    """

    CV_GROUNDED = "cv_grounded"
    UNBIASED = "unbiased"


class WorkAuthTier(StrEnum):
    """
    Tri-tier work authorization gating contract.

    ALL: No visa/citizenship restrictions applied.
    F1_OPT_CPT: Requires E-Verify confirmation and non-citizenship restriction.
    H1B_TRANSFER_SPONSOR: Positive job sponsorship + historical USCIS filings >= 5.
    DOMESTIC_ONLY: Restricts to US Citizens and Permanent Residents.
    """

    ALL = "all"
    F1_OPT_CPT = "f1_opt_cpt"
    H1B_TRANSFER_SPONSOR = "h1b_transfer_sponsor"
    DOMESTIC_ONLY = "domestic_only"


class WorkplaceModality(StrEnum):
    """Physical office requirement modality."""

    ALL = "all"
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"


class RemoteScopeTier(StrEnum):
    """Geographic hiring eligibility for remote roles."""

    GLOBAL = "worldwide_global"
    US_ONLY = "country_wide"
    STATE_SPECIFIC = "state_province"


class GeoCoordinateDTO(BaseModel):
    """Geographic coordinate representation for commute radius calculation."""

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    cbsa_metro_code: str | None = Field(None, max_length=16)
    state_code: str = Field("NV", max_length=2)


class JobSearchFilterDTO(BaseModel):
    """
    Unified Command-Facet search and discovery filter parameters.

    Strict Null-Safety Contract:
      Unselected controls or untouched sliders must default to None / ALL,
      generating zero restrictive SQL conditions.
    """

    # Search Engine Configuration
    search_mode: SearchMode = SearchMode.CV_GROUNDED
    raw_query: str | None = None

    # Tokenized Explicit Entities
    companies: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)

    # Visible Sticky Instrument Facets (None = Bypassed)
    work_auth_tier: WorkAuthTier = WorkAuthTier.ALL
    workplace_modality: WorkplaceModality = WorkplaceModality.ALL
    min_base_salary_usd: int | None = Field(default=None, ge=30000, le=500000)
    include_prevailing_wage_estimates: bool = True

    # Commute & Metro Boundary
    candidate_geo: GeoCoordinateDTO | None = None
    max_commute_miles: int | None = Field(default=None, ge=5, le=100)
    max_hybrid_days_in_office: int | None = Field(default=None, ge=1, le=5)

    # Domain & Transfer Modifiers
    domain_strictness: float = Field(default=0.5, ge=0.0, le=1.0)
    allow_asymmetric_skill_transfer: bool = True
    min_match_probability: float = Field(default=0.0, ge=0.0, le=1.0)

    # Pagination & Sorting
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="score", pattern="^(score|date|salary)$")


class SearchRelaxationDTO(BaseModel):
    """Diagnostic recommendation when zero results occur under strict filters."""

    restrictive_facet: str
    message: str
    action_label: str
    relaxed_patch: dict[str, Any]


class SearchDiagnosticsDTO(BaseModel):
    """Zero-dead-end diagnostic response identifying primary constraint bottlenecks."""

    status: str = "zero_results"
    primary_bottleneck: SearchRelaxationDTO | None = None
    all_relaxations: list[SearchRelaxationDTO] = Field(default_factory=list)


class TokenizedFilterExtractionDTO(BaseModel):
    """
    Result of parsing free-form search input into recognized entities
    and residual query text.
    """

    companies: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    seniority_levels: list[str] = Field(default_factory=list)
    workplace_modality: str | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    residual_query: str = ""
