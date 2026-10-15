"""
Candidate profile, multi-modal onboarding, multi-persona, and CV block CRUD API.

This router implements candidate profile workflows documented in ADR-001:
  - Document parsing endpoint (PDF, DOCX, LinkedIn PDF, text paste) returning
    staged CV blocks and extracted skills for user verification.
  - Interactive onboarding submission saving verified blocks, skills, and personas.
  - Multi-persona management (Universal Persona + specialized personas).
  - CV block CRUD operations (including hackathon achievements and quantified metrics).
"""

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.tools.embeddings import embed_text
from app.core.auth import DEFAULT_DEV_USER_ID, CurrentUser
from app.core.database import get_db
from app.ingestion.resume_parser import (
    ParsedCandidateData,
    ParsedCVBlock,
    parse_generic_resume_text,
    parse_resume_bytes,
)
from app.models.cv_block import CVBlock
from app.models.user_account import (
    CandidatePersona,
    PersonaCVBlockRel,
    PersonaSkill,
    UserAccount,
)
from app.models.user_profile import UserProfile
from app.services.diagnostics import (
    HolisticCandidateAudit,
    PersonaBenchmarkReport,
    generate_holistic_audit,
    generate_persona_market_benchmark,
)

logger = logging.getLogger("career_os.api.candidates")

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


class ParseTextRequest(BaseModel):
    """Payload for text-based resume or LinkedIn paste."""

    text: str = Field(..., min_length=20, examples=["Jane Doe\nSoftware Engineer..."])


class CreateSpecializedPersonaRequest(BaseModel):
    """Payload for creating a specialized target career persona."""

    name: str = Field(..., examples=["AI Platform Engineer"])
    headline: str | None = Field(None, examples=["Specializing in LLM Orchestration"])
    target_roles: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    seniority_level: str = Field(default="mid")
    years_experience: int = Field(default=3)
    skills: list[str] = Field(default_factory=list)


class OnboardingCommitRequest(BaseModel):
    """
    Payload for committing verified onboarding profile data to database.
    """

    full_name: str | None = None
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


class CVBlockResponse(BaseModel):
    """Response representing a persisted CVBlock entity."""

    id: str
    category: str
    title: str
    organization: str | None
    content: str
    metrics: dict[str, Any]
    skills: list[str]
    has_embedding: bool


class PersonaDetailResponse(BaseModel):
    """Detailed view of a candidate persona with skills and stats."""

    id: str
    name: str
    is_common_persona: bool
    headline: str | None
    seniority_level: str
    years_experience: int
    target_roles: list[str]
    target_industries: list[str]
    is_default: bool
    skill_count: int
    block_count: int


def _get_user_uuid(current_user: CurrentUser) -> uuid.UUID:
    try:
        return uuid.UUID(current_user.user_id)
    except ValueError:
        return uuid.UUID(DEFAULT_DEV_USER_ID)


async def _get_or_create_account(
    db: AsyncSession,
    user_uuid: uuid.UUID,
    email: str | None,
) -> UserAccount:
    stmt = (
        select(UserAccount)
        .options(selectinload(UserAccount.personas))
        .where(UserAccount.id == user_uuid)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account is None:
        account = UserAccount(
            id=user_uuid,
            email=email or f"user-{str(user_uuid)[:8]}@career-os.local",
            full_name="Candidate",
            visa_status="None",
            remote_preference="Remote",
            is_active=True,
        )
        db.add(account)
        await db.flush()

    return account


@router.post(
    "/parse-document",
    response_model=ParsedCandidateData,
    status_code=status.HTTP_200_OK,
)
async def parse_document_upload(
    file: Annotated[UploadFile, File(...)],
) -> ParsedCandidateData:
    """
    Parse an uploaded resume file (PDF, DOCX) and return structured staged data.
    """
    filename = file.filename or "resume.pdf"
    content_bytes = await file.read()

    if not content_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        parsed_data = parse_resume_bytes(content_bytes, filename)
        return parsed_data
    except Exception as exc:
        logger.error(f"Document parsing failed for '{filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse document layout: {exc}",
        ) from exc


@router.post(
    "/parse-text",
    response_model=ParsedCandidateData,
    status_code=status.HTTP_200_OK,
)
async def parse_pasted_text(
    req: ParseTextRequest,
) -> ParsedCandidateData:
    """
    Parse raw resume or LinkedIn text pasted by candidate.
    """
    try:
        return parse_generic_resume_text(req.text)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse pasted text: {exc}",
        ) from exc


@router.post(
    "/onboard",
    status_code=status.HTTP_200_OK,
)
async def commit_onboarding(
    req: OnboardingCommitRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict[str, Any]:
    """
    Commit verified onboarding qualifications to account, personas, and CV blocks.
    """
    user_uuid = _get_user_uuid(current_user)
    account = await _get_or_create_account(db, user_uuid, current_user.email)

    # 1. Update account level fields
    if req.full_name:
        account.full_name = req.full_name
    if req.visa_status:
        account.visa_status = req.visa_status
    if req.citizenship_country_code:
        account.citizenship_country_code = req.citizenship_country_code
    if req.preferred_locations:
        account.preferred_locations = req.preferred_locations
    if req.remote_preference:
        account.remote_preference = req.remote_preference

    # 2. Find or create Universal Persona
    stmt = select(CandidatePersona).where(
        CandidatePersona.user_account_id == account.id,
        CandidatePersona.is_common_persona.is_(True),
    )
    result = await db.execute(stmt)
    universal_persona = result.scalar_one_or_none()

    if universal_persona is None:
        universal_persona = CandidatePersona(
            id=uuid.uuid4(),
            user_account_id=account.id,
            name="Universal Profile",
            is_common_persona=True,
            is_default=True,
            headline=f"{account.full_name} — Universal Profile",
            target_roles=req.target_roles,
            target_industries=req.target_industries,
            years_experience=req.years_experience,
            seniority_level=req.seniority_level,
        )
        db.add(universal_persona)
        await db.flush()
    else:
        universal_persona.target_roles = req.target_roles
        universal_persona.target_industries = req.target_industries
        universal_persona.years_experience = req.years_experience
        universal_persona.seniority_level = req.seniority_level

    # 3. Also synchronize UserProfile for backward-compatibility
    prof_stmt = select(UserProfile).where(UserProfile.id == account.id)
    prof_res = await db.execute(prof_stmt)
    user_prof = prof_res.scalar_one_or_none()
    if user_prof is None:
        user_prof = UserProfile(
            id=account.id,
            user_account_id=account.id,
            email=account.email,
            full_name=account.full_name,
            visa_status=account.visa_status,
            remote_preference=account.remote_preference,
            tone_directives={},
            target_roles=req.target_roles,
            target_locations=account.preferred_locations,
        )
        db.add(user_prof)
        await db.flush()
    else:
        user_prof.full_name = account.full_name
        user_prof.visa_status = account.visa_status
        user_prof.target_roles = req.target_roles
        user_prof.target_locations = account.preferred_locations

    # 4. Ingest CV blocks with vector embeddings
    saved_blocks: list[CVBlock] = []
    for b in req.blocks:
        embedding = await embed_text(b.content)
        block = CVBlock(
            id=uuid.uuid4(),
            user_account_id=account.id,
            user_profile_id=account.id,
            category=b.category,
            title=b.title,
            organization=b.organization,
            content=b.content,
            metrics=b.metrics,
            skills=b.skills,
            embedding=embedding,
        )
        db.add(block)
        saved_blocks.append(block)

        # Link to Universal Persona
        rel = PersonaCVBlockRel(
            persona_id=universal_persona.id,
            cv_block_id=block.id,
            priority_weight=1.0,
            is_active=True,
        )
        db.add(rel)

    # 5. Ingest Skills into Universal Persona
    for s in req.skills:
        skill_name_clean = s.strip()
        if not skill_name_clean:
            continue
        skill_stmt = select(PersonaSkill).where(
            PersonaSkill.persona_id == universal_persona.id,
            PersonaSkill.skill_name == skill_name_clean,
        )
        skill_res = await db.execute(skill_stmt)
        if skill_res.scalar_one_or_none() is None:
            new_skill = PersonaSkill(
                id=uuid.uuid4(),
                persona_id=universal_persona.id,
                skill_name=skill_name_clean,
                category="tool",
                proficiency="intermediate",
                years_experience=max(1, req.years_experience),
                is_core=True,
            )
            db.add(new_skill)

    # 6. Ingest Specialized Personas if provided
    created_spec_count = 0
    for spec_req in req.specialized_personas:
        spec_persona = CandidatePersona(
            id=uuid.uuid4(),
            user_account_id=account.id,
            name=spec_req.name,
            is_common_persona=False,
            is_default=False,
            headline=spec_req.headline,
            target_roles=spec_req.target_roles,
            target_industries=spec_req.target_industries,
            years_experience=spec_req.years_experience,
            seniority_level=spec_req.seniority_level,
        )
        db.add(spec_persona)
        await db.flush()
        created_spec_count += 1

        # Link specific skills to specialized persona
        for s in spec_req.skills:
            db.add(
                PersonaSkill(
                    id=uuid.uuid4(),
                    persona_id=spec_persona.id,
                    skill_name=s.strip(),
                    category="tool",
                    proficiency="advanced",
                    years_experience=spec_req.years_experience,
                    is_core=True,
                )
            )

        # Link blocks that match specialized persona skills
        spec_skills_lower = {s.lower() for s in spec_req.skills}
        for block in saved_blocks:
            block_skills_lower = {bs.lower() for bs in (block.skills or [])}
            if spec_skills_lower.intersection(block_skills_lower):
                db.add(
                    PersonaCVBlockRel(
                        persona_id=spec_persona.id,
                        cv_block_id=block.id,
                        priority_weight=1.5,
                        is_active=True,
                    )
                )

    await db.commit()

    return {
        "status": "onboarded",
        "user_id": str(account.id),
        "universal_persona_id": str(universal_persona.id),
        "blocks_ingested": len(saved_blocks),
        "skills_ingested": len(req.skills),
        "specialized_personas_created": created_spec_count,
    }


@router.get(
    "/personas",
    response_model=list[PersonaDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def list_personas(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> list[PersonaDetailResponse]:
    """
    List all career personas associated with the current candidate account.
    """
    user_uuid = _get_user_uuid(current_user)

    stmt = (
        select(CandidatePersona)
        .options(
            selectinload(CandidatePersona.skills),
            selectinload(CandidatePersona.cv_block_rels),
        )
        .where(CandidatePersona.user_account_id == user_uuid)
        .order_by(
            CandidatePersona.is_common_persona.desc(),
            CandidatePersona.is_default.desc(),
        )
    )
    result = await db.execute(stmt)
    personas = result.scalars().all()

    return [
        PersonaDetailResponse(
            id=str(p.id),
            name=p.name,
            is_common_persona=p.is_common_persona,
            headline=p.headline,
            seniority_level=p.seniority_level,
            years_experience=p.years_experience,
            target_roles=list(p.target_roles or []),
            target_industries=list(p.target_industries or []),
            is_default=p.is_default,
            skill_count=len(p.skills or []),
            block_count=len(p.cv_block_rels or []),
        )
        for p in personas
    ]


@router.post(
    "/personas",
    response_model=PersonaDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_persona(
    req: CreateSpecializedPersonaRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> PersonaDetailResponse:
    """
    Create a new specialized candidate persona.
    """
    user_uuid = _get_user_uuid(current_user)
    account = await _get_or_create_account(db, user_uuid, current_user.email)

    persona_id = uuid.uuid4()
    persona = CandidatePersona(
        id=persona_id,
        user_account_id=account.id,
        name=req.name.strip(),
        is_common_persona=False,
        is_default=False,
        headline=req.headline,
        target_roles=req.target_roles,
        target_industries=req.target_industries,
        seniority_level=req.seniority_level,
        years_experience=req.years_experience,
    )
    db.add(persona)

    # Attach declared skills
    for s in req.skills:
        db.add(
            PersonaSkill(
                id=uuid.uuid4(),
                persona_id=persona_id,
                skill_name=s.strip(),
                category="tool",
                proficiency="advanced",
                years_experience=req.years_experience,
                is_core=True,
            )
        )

    await db.commit()

    return PersonaDetailResponse(
        id=str(persona_id),
        name=persona.name,
        is_common_persona=persona.is_common_persona,
        headline=persona.headline,
        seniority_level=persona.seniority_level,
        years_experience=persona.years_experience,
        target_roles=list(persona.target_roles or []),
        target_industries=list(persona.target_industries or []),
        is_default=persona.is_default,
        skill_count=len(req.skills),
        block_count=0,
    )


@router.put(
    "/personas/{persona_id}/default",
    status_code=status.HTTP_200_OK,
)
async def set_default_persona(
    persona_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict[str, str]:
    """
    Designate a persona as the primary active default on candidate login.
    """
    user_uuid = _get_user_uuid(current_user)
    p_uuid = uuid.UUID(persona_id)

    # Reset all personas to not default
    await db.execute(
        update(CandidatePersona)
        .where(CandidatePersona.user_account_id == user_uuid)
        .values(is_default=False)
    )

    # Set target persona as default
    await db.execute(
        update(CandidatePersona)
        .where(
            CandidatePersona.id == p_uuid,
            CandidatePersona.user_account_id == user_uuid,
        )
        .values(is_default=True)
    )
    await db.commit()

    return {"status": "success", "default_persona_id": persona_id}


@router.get(
    "/audit",
    response_model=HolisticCandidateAudit,
    status_code=status.HTTP_200_OK,
)
async def get_candidate_audit(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> HolisticCandidateAudit:
    """
    Tier 0: Return holistic 360° candidate evaluation and market diagnostics.
    """
    user_uuid = _get_user_uuid(current_user)
    await _get_or_create_account(db, user_uuid, current_user.email)
    try:
        return await generate_holistic_audit(db, user_uuid)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/personas/{persona_id}/benchmark",
    response_model=PersonaBenchmarkReport,
    status_code=status.HTTP_200_OK,
)
async def get_persona_benchmark(
    persona_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> PersonaBenchmarkReport:
    """
    Tier 2: Return macro-level market benchmarks and skill gaps for target persona.
    """
    try:
        p_uuid = uuid.UUID(persona_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid persona_id UUID format.",
        ) from err

    try:
        return await generate_persona_market_benchmark(db, p_uuid)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/blocks",
    response_model=list[CVBlockResponse],
    status_code=status.HTTP_200_OK,
)
async def list_cv_blocks(
    current_user: CurrentUser,
    db: DatabaseSession,
    persona_id: str | None = Query(None, description="Filter by persona linkage"),
) -> list[CVBlockResponse]:
    """
    Retrieve candidate CV blocks, optionally filtered by persona inclusion.
    """
    user_uuid = _get_user_uuid(current_user)

    if persona_id:
        p_uuid = uuid.UUID(persona_id)
        stmt = (
            select(CVBlock)
            .join(PersonaCVBlockRel, PersonaCVBlockRel.cv_block_id == CVBlock.id)
            .where(
                CVBlock.user_account_id == user_uuid,
                PersonaCVBlockRel.persona_id == p_uuid,
                PersonaCVBlockRel.is_active.is_(True),
            )
        )
    else:
        stmt = select(CVBlock).where(CVBlock.user_account_id == user_uuid)

    result = await db.execute(stmt)
    blocks = result.scalars().all()

    return [
        CVBlockResponse(
            id=str(b.id),
            category=b.category,
            title=b.title,
            organization=b.organization,
            content=b.content,
            metrics=dict(b.metrics or {}),
            skills=list(b.skills or []),
            has_embedding=b.embedding is not None,
        )
        for b in blocks
    ]


@router.post(
    "/blocks",
    response_model=CVBlockResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cv_block(
    req: CVBlockCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CVBlockResponse:
    """
    Add a new master CV block and compute its vector embedding.
    """
    user_uuid = _get_user_uuid(current_user)
    account = await _get_or_create_account(db, user_uuid, current_user.email)

    embedding = await embed_text(req.content)
    block_id = uuid.uuid4()
    block = CVBlock(
        id=block_id,
        user_account_id=account.id,
        user_profile_id=account.id,
        category=req.category,
        title=req.title,
        organization=req.organization,
        content=req.content,
        metrics=req.metrics,
        skills=req.skills,
        embedding=embedding,
    )
    db.add(block)

    # Link to specified personas or Universal Persona by default
    target_persona_uuids: list[uuid.UUID] = []
    if req.persona_ids:
        target_persona_uuids = [uuid.UUID(pid) for pid in req.persona_ids]
    else:
        # Default to Universal Persona
        u_stmt = select(CandidatePersona.id).where(
            CandidatePersona.user_account_id == account.id,
            CandidatePersona.is_common_persona.is_(True),
        )
        u_res = await db.execute(u_stmt)
        u_id = u_res.scalar_one_or_none()
        if u_id:
            target_persona_uuids.append(u_id)

    for p_id in target_persona_uuids:
        db.add(
            PersonaCVBlockRel(
                persona_id=p_id,
                cv_block_id=block_id,
                priority_weight=1.0,
                is_active=True,
            )
        )

    await db.commit()

    return CVBlockResponse(
        id=str(block.id),
        category=block.category,
        title=block.title,
        organization=block.organization,
        content=block.content,
        metrics=dict(block.metrics or {}),
        skills=list(block.skills or []),
        has_embedding=True,
    )


@router.delete(
    "/blocks/{block_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_cv_block(
    block_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict[str, str]:
    """
    Delete a CV block and its persona junction links.
    """
    user_uuid = _get_user_uuid(current_user)
    b_uuid = uuid.UUID(block_id)

    # Verify block exists and belongs to user
    b_stmt = select(CVBlock).where(
        CVBlock.id == b_uuid,
        CVBlock.user_account_id == user_uuid,
    )
    b_res = await db.execute(b_stmt)
    block = b_res.scalar_one_or_none()
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV block not found or access denied.",
        )

    # Delete junction rels first
    await db.execute(
        delete(PersonaCVBlockRel).where(PersonaCVBlockRel.cv_block_id == b_uuid)
    )

    await db.delete(block)
    await db.commit()
    return {"status": "deleted", "block_id": block_id}
