"""
UserAccount, CandidatePersona, PersonaSkill, PersonaCVBlockRel, and JobMatchCache.

This module implements the multi-persona candidate modeling layer documented in:
  - ADR-007: Candidate Modeling, Multi-Modal Ingestion & Multi-Persona Architecture
  - ADR-008: High-Probability Job Matching, Two-Stage Retrieval & Fault-Tolerant Ranking

Architecture Overview:
  - ``UserAccount``: Central authentication identity, legal work authorization
    (visa status), citizenship, and account-level search constraints.
  - ``CandidatePersona``: Multiple target career profiles owned by a single account
    (e.g., Universal Profile, AI Platform Engineer, Python Backend).
  - ``PersonaSkill``: Normalized skill matrix per persona with proficiency tiers.
  - ``PersonaCVBlockRel``: Junction table mapping master career achievement blocks
    (``cv_block``) to specific candidate personas with relative priority weights.
  - ``JobMatchCache``: Persisted scoring diagnostics and matching telemetry per
    persona-job pair.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, utc_now

if TYPE_CHECKING:
    from app.models.cv_block import CVBlock
    from app.models.job_listing import JobListing
    from app.models.user_profile import UserProfile


class UserAccount(Base, UUIDMixin, TimestampMixin):
    """
    Central authentication identity and master candidate account.

    Attributes:
        email: Unique indexed user email used for authentication.
        password_hash: Salted hash of candidate password (bcrypt or argon2).
        full_name: Legal or professional candidate name.
        visa_status: Primary work authorization (e.g. 'Citizen', 'H-1B', 'F-1 OPT').
        citizenship_country_code: Two-letter ISO country code (e.g. 'US', 'IN', 'CA').
        preferred_locations: JSON list of target metropolitan areas or remote codes.
        remote_preference: Workplace policy preference ('Remote', 'Hybrid', 'On-site').
        is_active: Account status flag for soft deactivation.
        personas: One-to-many relationship to specialized career personas.
        cv_blocks: One-to-many relationship to master career achievement blocks.
        user_profiles: One-to-many relationship to legacy/agent user profile instances.
    """

    __tablename__ = "user_account"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    visa_status: Mapped[str] = mapped_column(
        String(100), default="None", index=True, nullable=False
    )
    citizenship_country_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )
    preferred_locations: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    remote_preference: Mapped[str] = mapped_column(
        String(50), default="Remote", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    personas: Mapped[list["CandidatePersona"]] = relationship(
        "CandidatePersona",
        back_populates="user_account",
    )
    cv_blocks: Mapped[list["CVBlock"]] = relationship(
        "CVBlock",
        back_populates="user_account",
    )
    user_profiles: Mapped[list["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user_account",
    )


class CandidatePersona(Base, UUIDMixin, TimestampMixin):
    """
    Target career persona representing a specialized professional lens.

    Every user account possesses at least one Universal / Common Persona
    (``is_common_persona = TRUE``) that aggregates all competencies to discover
    hybrid opportunities, alongside optional specialized personas (e.g. AI Platform).

    Attributes:
        user_account_id: Foreign key to parent user account (ON DELETE RESTRICT).
        name: Persona title (e.g. 'Universal Profile', 'AI Platform Engineer').
        is_common_persona: True if this persona is the universal aggregate profile.
        headline: Professional elevator pitch or resume headline.
        target_roles: JSON list of specific job titles targeted by this persona.
        target_industries: JSON list of target sector codes from industry_sector.
        years_experience: Total calibrated years of relevant experience.
        seniority_level: Calibrated seniority tier ('junior', 'mid', 'senior', etc.).
        min_salary: Optional annual compensation floor.
        is_default: True if this persona is the active default on login.
        skills: One-to-many relationship to skills mapped to this persona.
        cv_block_rels: One-to-many relationship to junction mappings for cv_blocks.
        matches: One-to-many relationship to cached job match evaluations.
    """

    __tablename__ = "candidate_persona"

    user_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_account.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_common_persona: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=False
    )
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    target_industries: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    years_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seniority_level: Mapped[str] = mapped_column(
        String(50), default="mid", nullable=False
    )
    min_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user_account: Mapped["UserAccount"] = relationship(
        "UserAccount",
        back_populates="personas",
    )
    skills: Mapped[list["PersonaSkill"]] = relationship(
        "PersonaSkill",
        back_populates="persona",
    )
    cv_block_rels: Mapped[list["PersonaCVBlockRel"]] = relationship(
        "PersonaCVBlockRel",
        back_populates="persona",
    )
    matches: Mapped[list["JobMatchCache"]] = relationship(
        "JobMatchCache",
        back_populates="persona",
    )


class PersonaSkill(Base, UUIDMixin):
    """
    Normalized technical and domain competency assigned to a candidate persona.

    Attributes:
        persona_id: Foreign key to candidate persona (ON DELETE RESTRICT).
        skill_name: Canonical skill token (e.g. 'Python', 'FastAPI', 'Apache Kafka').
        category: Competency domain ('language', 'framework', 'tool', 'database').
        proficiency: Mastery rating ('beginner', 'intermediate', 'advanced', 'expert').
        years_experience: Years of hands-on experience with this skill.
        is_core: True if this skill is non-negotiable core competency for persona.
        created_at: Creation audit timestamp.
    """

    __tablename__ = "persona_skill"
    __table_args__ = (
        UniqueConstraint("persona_id", "skill_name", name="uq_persona_skill_unique"),
    )

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_persona.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="tool", nullable=False)
    proficiency: Mapped[str] = mapped_column(
        String(50), default="intermediate", nullable=False
    )
    years_experience: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_core: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    persona: Mapped["CandidatePersona"] = relationship(
        "CandidatePersona",
        back_populates="skills",
    )


class PersonaCVBlockRel(Base):
    """
    Junction association table linking master CVBlocks to specific CandidatePersonas.

    Enables personas to selectively include, exclude, and prioritize specific
    career achievements (e.g. emphasizing distributed systems projects for backend
    roles and research publications for AI roles).

    Attributes:
        persona_id: Foreign key to CandidatePersona (part of composite PK).
        cv_block_id: Foreign key to CVBlock (part of composite PK).
        priority_weight: Multiplier (0.1 - 2.0) for semantic retrieval ranking.
        is_active: Toggle to temporarily suppress block from persona's tailored CVs.
    """

    __tablename__ = "persona_cv_block_rel"

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_persona.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    cv_block_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cv_block.id", ondelete="RESTRICT"),
        primary_key=True,
        index=True,
    )
    priority_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    persona: Mapped["CandidatePersona"] = relationship(
        "CandidatePersona",
        back_populates="cv_block_rels",
    )
    cv_block: Mapped["CVBlock"] = relationship(
        "CVBlock",
        back_populates="persona_rels",
    )


class JobMatchCache(Base, UUIDMixin):
    """
    Persisted match evaluation cache and diagnostics for persona-job pairs.

    Stores the calculated Acceptance Probability Score P(Match) along with
    decomposed factors (semantic relevance, skill overlap, prestige, achievements)
    and missing dealbreakers to eliminate duplicate scoring overhead.

    Attributes:
        persona_id: Foreign key to evaluated CandidatePersona.
        job_listing_id: Foreign key to target JobListing.
        match_score: Composite acceptance probability P(Match) in [0.0, 1.0].
        hard_gate_pass: True if hard requirements (visa, geography) passed.
        skill_overlap_score: Fractional overlap of candidate skills vs job reqs.
        semantic_score: Cosine similarity score between CV blocks and job description.
        seniority_score: Alignment score between candidate experience and seniority.
        prestige_booster: Additional multiplier for Tier-1 employers or universities.
        achievement_booster: Multiplier for hackathon wins or open-source honors.
        missing_skills: JSON list of required technologies absent from the persona.
        matched_skills: JSON list of overlapping technologies confirmed in profile.
        evaluated_at: Timestamp of scoring computation.
    """

    __tablename__ = "job_match_cache"
    __table_args__ = (
        UniqueConstraint("persona_id", "job_listing_id", name="uq_persona_job_match"),
    )

    persona_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_persona.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    job_listing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_listing.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hard_gate_pass: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    skill_overlap_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    seniority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    prestige_booster: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    achievement_booster: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    missing_skills: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    matched_skills: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    persona: Mapped["CandidatePersona"] = relationship(
        "CandidatePersona",
        back_populates="matches",
    )
    job_listing: Mapped["JobListing"] = relationship(
        "JobListing",
        back_populates="match_caches",
    )
