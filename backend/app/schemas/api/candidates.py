"""
Request and response Pydantic DTOs for candidate persona onboarding and profile management.
"""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.candidate_dossier import ParsedCVBlock


class ParseTextRequest(BaseModel):
    """Payload for text-based resume or LinkedIn paste."""

    text: str = Field(..., min_length=20, examples=["Jane Doe\nSoftware Engineer..."])


class CreateSpecializedPersonaRequest(BaseModel):
    """Payload for creating a specialized target career persona."""

    name: str = Field(..., examples=["AI Platform Engineer"])
    headline: str | None = Field(None, examples=["Specializing in LLM Orchestration"])
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    seniority_level: str = Field(default="entry")
    years_experience: int = Field(default=0, ge=0)
    skills: list[str] = Field(default_factory=list)
    clone_from_persona_id: str | None = None
    career_intelligence: dict[str, Any] = Field(default_factory=dict)


class UpdatePersonaRequest(BaseModel):
    """Payload for updating or renaming a candidate persona."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["AI Platform Engineer"],
    )
    headline: str | None = Field(
        None,
        max_length=255,
        examples=["Specializing in Large-Scale AI Orchestration"],
    )
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    seniority_level: str = Field(default="mid")
    years_experience: int = Field(default=0, ge=0)
    min_salary: int | None = Field(default=None, ge=0)
    skills: list[str] = Field(default_factory=list)
    career_intelligence: dict[str, Any] = Field(default_factory=dict)
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    visa_status: str | None = None
    preferred_locations: list[str] | None = None
    remote_preference: str | None = None


class OnboardingCommitRequest(BaseModel):
    """
    Payload for committing verified onboarding profile data to database.
    """

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    visa_status: str | None = None
    citizenship_country_code: str | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: str = "Remote"
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    years_experience: int = 0
    seniority_level: str = "mid"
    skills: list[str] = Field(default_factory=list)
    blocks: list[ParsedCVBlock] = Field(default_factory=list)
    career_intelligence: dict[str, Any] = Field(default_factory=dict)
    specialized_personas: list[CreateSpecializedPersonaRequest] = Field(
        default_factory=list
    )


class CVBlockCreateRequest(BaseModel):
    """Payload for adding a new master CV achievement block."""

    category: str = Field(
        default="experience",
        examples=["experience", "project", "hackathon_achievement", "open_source"],
    )
    title: str = Field(..., examples=["Distributed Model Inference Engine"])
    organization: str | None = Field(None, examples=["ETHGlobal Hackathon"])
    content: str = Field(
        ...,
        examples=["Architected low-latency worker queue processing 50k req/s."],
    )
    metrics: dict[str, Any] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    persona_ids: list[str] = Field(default_factory=list)
    content_fingerprint: str | None = None


class CVBlockUpdateRequest(BaseModel):
    """Payload for updating an existing master CV achievement block."""

    category: str | None = None
    title: str | None = None
    organization: str | None = None
    content: str | None = None
    metrics: dict[str, Any] | None = None
    skills: list[str] | None = None


class CVBlockResponse(BaseModel):
    """Response representing a persisted CVBlock entity."""

    id: str
    category: str
    title: str
    organization: str | None
    content: str
    metrics: dict[str, Any]
    skills: list[str]
    content_fingerprint: str | None = None
    has_embedding: bool


class PersonaDetailResponse(BaseModel):
    """Detailed view of a candidate persona with skills and stats."""

    id: str
    name: str
    is_common_persona: bool
    headline: str | None
    seniority_level: str
    years_experience: int
    min_salary: int | None = None
    target_roles: list[str]
    target_industries: list[str]
    is_default: bool
    skill_count: int
    block_count: int
    skills: list[str] = Field(default_factory=list)
    career_intelligence: dict[str, Any] = Field(default_factory=dict)
    completeness: dict[str, Any] = Field(default_factory=dict)
    completeness_score: int = 0
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    visa_status: str | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: str = "Remote"
