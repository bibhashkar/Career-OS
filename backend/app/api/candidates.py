"""
Candidate profile, multi-modal onboarding, multi-persona, and CV block CRUD API.

This router implements candidate profile workflows documented in ADR-007:
  - Document parsing endpoint (PDF, DOCX, LinkedIn PDF, text paste) returning
    staged CV blocks and extracted skills for user verification.
  - Interactive onboarding submission saving verified blocks, skills, and personas.
  - Multi-persona management (Universal Persona + specialized personas).
  - CV block CRUD operations (including hackathon achievements and quantified metrics).
"""

import logging
import uuid
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.tools.embeddings import embed_text, embed_texts
from app.core.auth import DEFAULT_DEV_USER_ID, CurrentUser
from app.core.database import get_db
from app.core.helpers import parse_uuid_or_400
from app.ingestion.resume_parser import (
    ParsedCandidateData,
    extract_quantified_metrics,
    extract_skills_from_text,
    parse_generic_resume_text,
    parse_resume_bytes,
)
from app.models.cv_block import CVBlock
from app.models.user_account import (
    CandidatePersona,
    JobMatchCache,
    PersonaCVBlockRel,
    PersonaSkill,
    UserAccount,
)
from app.models.user_profile import UserProfile
from app.schemas.api.candidates import (
    CreateSpecializedPersonaRequest as CreateSpecializedPersonaRequest,
)
from app.schemas.api.candidates import (
    CVBlockCreateRequest as CVBlockCreateRequest,
)
from app.schemas.api.candidates import (
    CVBlockResponse as CVBlockResponse,
)
from app.schemas.api.candidates import (
    CVBlockUpdateRequest as CVBlockUpdateRequest,
)
from app.schemas.api.candidates import (
    OnboardingCommitRequest as OnboardingCommitRequest,
)
from app.schemas.api.candidates import (
    ParseTextRequest as ParseTextRequest,
)
from app.schemas.api.candidates import (
    PersonaDetailResponse as PersonaDetailResponse,
)
from app.schemas.api.candidates import (
    UpdatePersonaRequest as UpdatePersonaRequest,
)
from app.schemas.candidate_dossier import (
    compute_bullet_fingerprint,
    normalize_award_record,
    normalize_institution_tier,
)
from app.services.diagnostics import (
    HolisticCandidateAudit,
    PersonaBenchmarkReport,
    calculate_persona_completeness,
    generate_holistic_audit,
    generate_persona_market_benchmark,
)

logger = logging.getLogger("career_os.api.candidates")

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def _build_persona_detail_response(
    persona: CandidatePersona,
    account: UserAccount | None = None,
    blocks: list[Any] | None = None,
) -> PersonaDetailResponse:
    skill_names = [s.skill_name for s in (persona.skills or [])]
    cv_blocks = blocks or []
    career_intel = dict(persona.career_intelligence or {})
    visa = getattr(account, "visa_status", None)
    locs = list(getattr(account, "preferred_locations", []) or [])
    remote = getattr(account, "remote_preference", "Remote") or "Remote"
    acc_name = getattr(account, "full_name", None)
    acc_email = getattr(account, "email", None)
    acc_phone = getattr(account, "phone", None)

    pii = dict(career_intel.get("contact_pii") or {})

    # Prioritize candidate-verified contact PII over generic default account strings
    f_name = (
        pii.get("full_name")
        if pii.get("full_name") and pii.get("full_name") != "Candidate"
        else None
    ) or (
        acc_name
        if acc_name and acc_name != "Candidate"
        else (pii.get("full_name") or acc_name)
    )

    u_email = pii.get("email") or acc_email
    u_phone = pii.get("phone") or acc_phone

    # Ensure career_intel['contact_pii'] reflects the unified contact info
    career_intel["contact_pii"] = {
        "full_name": f_name,
        "email": u_email,
        "phone": u_phone,
    }

    # Normalize education institution_tier values on read
    raw_edu = career_intel.get("education")
    if isinstance(raw_edu, list):
        norm_edu: list[dict[str, Any]] = []
        for ed in raw_edu:
            if isinstance(ed, dict):
                ed_copy = dict(ed)
                ed_copy["institution_tier"] = normalize_institution_tier(
                    ed_copy.get("institution_tier")
                )
                norm_edu.append(ed_copy)
        career_intel["education"] = norm_edu

    # Normalize awards_recognitions records on read
    raw_awards = career_intel.get("awards_recognitions")
    if isinstance(raw_awards, list):
        career_intel["awards_recognitions"] = [
            normalize_award_record(aw) for aw in raw_awards if isinstance(aw, dict)
        ]

    # Backfill quantified metrics on work_experience bullets if empty
    raw_work = career_intel.get("work_experience")
    if isinstance(raw_work, list):
        norm_work: list[dict[str, Any]] = []
        for w in raw_work:
            if not isinstance(w, dict):
                continue
            w_copy = dict(w)
            raw_bullets = w_copy.get("bullets")
            if isinstance(raw_bullets, list):
                norm_bullets: list[dict[str, Any]] = []
                for b in raw_bullets:
                    if not isinstance(b, dict):
                        continue
                    b_copy = dict(b)
                    if not b_copy.get("metrics") and b_copy.get("raw_text"):
                        extracted_m = extract_quantified_metrics(
                            str(b_copy.get("raw_text") or "")
                        )
                        if extracted_m:
                            b_copy["metrics"] = [m.model_dump() for m in extracted_m]
                    norm_bullets.append(b_copy)
                w_copy["bullets"] = norm_bullets
            norm_work.append(w_copy)
        career_intel["work_experience"] = norm_work

    completeness = calculate_persona_completeness(
        target_roles=list(persona.target_roles or []),
        years_experience=persona.years_experience,
        seniority_level=persona.seniority_level,
        skills=skill_names,
        blocks=cv_blocks,
        career_intelligence=career_intel,
        visa_status=visa,
        preferred_locations=locs,
        min_salary=persona.min_salary,
    )

    return PersonaDetailResponse(
        id=str(persona.id),
        name=persona.name,
        is_common_persona=persona.is_common_persona,
        headline=persona.headline,
        seniority_level=persona.seniority_level,
        years_experience=persona.years_experience,
        min_salary=persona.min_salary,
        target_roles=list(persona.target_roles or []),
        target_industries=list(persona.target_industries or []),
        is_default=persona.is_default,
        skill_count=len(skill_names),
        block_count=len(persona.cv_block_rels or [])
        if blocks is None
        else len(cv_blocks),
        skills=skill_names,
        career_intelligence=career_intel,
        completeness=completeness.model_dump(),
        completeness_score=completeness.score,
        full_name=f_name,
        email=u_email,
        phone=u_phone,
        visa_status=visa,
        preferred_locations=locs,
        remote_preference=remote,
    )


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

    # Synchronize corresponding UserProfile to satisfy legacy foreign key constraints
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
            target_roles=[],
            target_locations=[],
        )
        db.add(user_prof)
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
    if req.full_name and req.full_name.strip():
        account.full_name = req.full_name.strip()
    if req.phone and req.phone.strip():
        account.phone = req.phone.strip()
    if (
        req.email
        and req.email.strip()
        and req.email.strip().lower() != account.email.lower()
    ):
        dup_acc_stmt = select(UserAccount.id).where(
            func.lower(UserAccount.email) == req.email.strip().lower(),
            UserAccount.id != user_uuid,
        )
        if not (await db.execute(dup_acc_stmt)).scalar_one_or_none():
            account.email = req.email.strip()
    if req.visa_status:
        account.visa_status = req.visa_status
    if req.citizenship_country_code:
        account.citizenship_country_code = req.citizenship_country_code
    if req.preferred_locations:
        account.preferred_locations = req.preferred_locations
    if req.remote_preference:
        account.remote_preference = req.remote_preference

    resolved_pii = {
        "full_name": account.full_name,
        "email": req.email or account.email,
        "phone": account.phone,
    }

    # 2. Find or create Universal Persona
    stmt = select(CandidatePersona).where(
        CandidatePersona.user_account_id == account.id,
        CandidatePersona.is_common_persona.is_(True),
    )
    result = await db.execute(stmt)
    universal_persona = result.scalar_one_or_none()

    if universal_persona is None:
        init_ci = dict(req.career_intelligence or {})
        init_ci["contact_pii"] = resolved_pii
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
            career_intelligence=init_ci,
        )
        db.add(universal_persona)
        await db.flush()
    else:
        universal_persona.target_roles = req.target_roles
        universal_persona.target_industries = req.target_industries
        universal_persona.years_experience = req.years_experience
        universal_persona.seniority_level = req.seniority_level
        ci = dict(
            req.career_intelligence or universal_persona.career_intelligence or {}
        )
        ci["contact_pii"] = resolved_pii
        universal_persona.career_intelligence = ci

    # 3. Also synchronize UserProfile for backward-compatibility
    prof_stmt = select(UserProfile).where(
        or_(
            UserProfile.user_account_id == account.id,
            UserProfile.id == account.id,
        )
    )
    prof_res = await db.execute(prof_stmt)
    user_prof = prof_res.scalars().first()
    if user_prof is None:
        user_prof = UserProfile(
            id=account.id,
            user_account_id=account.id,
            email=account.email,
            phone=account.phone,
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
        user_prof.phone = account.phone
        user_prof.visa_status = account.visa_status
        user_prof.target_roles = req.target_roles
        user_prof.target_locations = account.preferred_locations

    # 4. Ingest CV blocks with vector embeddings in batch (deduplicated by content_fingerprint)
    saved_blocks: list[CVBlock] = []
    block_contents = [b.content for b in req.blocks]
    block_embeddings = await embed_texts(block_contents) if block_contents else []

    for b, embedding in zip(req.blocks, block_embeddings, strict=False):
        b_fp = b.content_fingerprint or compute_bullet_fingerprint(
            str(account.id), b.organization, b.content
        )
        existing_stmt = select(CVBlock).where(
            CVBlock.user_account_id == account.id,
            CVBlock.content_fingerprint == b_fp,
        )
        existing_block = (await db.execute(existing_stmt)).scalars().first()
        if existing_block:
            block = existing_block
            if b.metrics:
                m_copy = dict(block.metrics or {})
                m_copy.update(b.metrics)
                block.metrics = m_copy
            if b.skills:
                s_copy = set(block.skills or [])
                s_copy.update(b.skills)
                block.skills = sorted(s_copy)
        else:
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
                content_fingerprint=b_fp,
                embedding=embedding,
            )
            db.add(block)
        saved_blocks.append(block)

        # Link to Universal Persona if not already linked
        rel_check = select(PersonaCVBlockRel).where(
            PersonaCVBlockRel.persona_id == universal_persona.id,
            PersonaCVBlockRel.cv_block_id == block.id,
        )
        if (await db.execute(rel_check)).scalars().first() is None:
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
                years_experience=req.years_experience or 0,
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

    acc_stmt = select(UserAccount).where(UserAccount.id == user_uuid)
    account = (await db.execute(acc_stmt)).scalar_one_or_none()

    return [_build_persona_detail_response(p, account=account) for p in personas]


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
    Create or update the unified candidate persona.
    Enforces single-profile mode across all users (including admin right now).
    """
    user_uuid = _get_user_uuid(current_user)
    account = await _get_or_create_account(db, user_uuid, current_user.email)

    clean_name = req.name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Persona name cannot be empty.",
        )

    # Check for duplicate name among user's personas
    dup_stmt = select(CandidatePersona).where(
        CandidatePersona.user_account_id == account.id,
        func.lower(CandidatePersona.name) == clean_name.lower(),
    )
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"A persona with the name '{clean_name}' already exists "
                "for this account."
            ),
        )

    persona_id = uuid.uuid4()
    cloned_ci: dict[str, Any] = dict(req.career_intelligence or {})
    source_persona = None
    if req.clone_from_persona_id:
        try:
            s_uuid = uuid.UUID(req.clone_from_persona_id)
            source_stmt = (
                select(CandidatePersona)
                .options(
                    selectinload(CandidatePersona.skills),
                    selectinload(CandidatePersona.cv_block_rels),
                )
                .where(
                    CandidatePersona.id == s_uuid,
                    CandidatePersona.user_account_id == account.id,
                )
            )
            source_persona = (await db.execute(source_stmt)).scalar_one_or_none()
            if source_persona:
                cloned_ci = dict(source_persona.career_intelligence or {})
                if req.career_intelligence:
                    cloned_ci.update(req.career_intelligence)
        except ValueError:
            pass

    persona = CandidatePersona(
        id=persona_id,
        user_account_id=account.id,
        name=clean_name,
        is_common_persona=False,
        is_default=False,
        headline=req.headline or (source_persona.headline if source_persona else None),
        target_roles=req.target_roles
        or (list(source_persona.target_roles) if source_persona else []),
        target_industries=req.target_industries
        or (list(source_persona.target_industries) if source_persona else []),
        seniority_level=req.seniority_level
        if req.seniority_level != "entry"
        else (source_persona.seniority_level if source_persona else "entry"),
        years_experience=req.years_experience
        or (source_persona.years_experience if source_persona else 0),
        career_intelligence=cloned_ci,
    )
    db.add(persona)

    # Attach declared skills (or clone from source)
    target_skills = list(req.skills)
    if not target_skills and source_persona and source_persona.skills:
        target_skills = [s.skill_name for s in source_persona.skills]

    for s in target_skills:
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

    # Clone active CV block relations if cloning
    if source_persona and source_persona.cv_block_rels:
        for rel in source_persona.cv_block_rels:
            if rel.is_active:
                db.add(
                    PersonaCVBlockRel(
                        persona_id=persona_id,
                        cv_block_id=rel.cv_block_id,
                        priority_weight=rel.priority_weight,
                        is_active=True,
                    )
                )

    await db.commit()
    await db.refresh(persona, attribute_names=["skills", "cv_block_rels"])

    return _build_persona_detail_response(persona, account=account)


@router.put(
    "/personas/{persona_id}",
    response_model=PersonaDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def update_persona(
    persona_id: str,
    req: UpdatePersonaRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> PersonaDetailResponse:
    """
    Update or rename a candidate persona.

    Guards:
      - Universal Profile name is fixed and cannot be renamed.
      - Case-insensitive uniqueness for persona names per candidate account.
    """
    user_uuid = _get_user_uuid(current_user)
    p_uuid = parse_uuid_or_400(persona_id, "persona_id")

    stmt = (
        select(CandidatePersona)
        .options(
            selectinload(CandidatePersona.skills),
            selectinload(CandidatePersona.cv_block_rels),
        )
        .where(
            CandidatePersona.id == p_uuid,
            CandidatePersona.user_account_id == user_uuid,
        )
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found or access denied.",
        )

    clean_name = req.name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Persona name cannot be empty.",
        )

    # 1. Enforce that Universal Persona cannot be renamed
    if persona.is_common_persona and clean_name.lower() != persona.name.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The Universal Profile name is fixed and cannot be renamed.",
        )

    # 2. Check for duplicate name among other personas of this account
    if clean_name.lower() != persona.name.lower():
        dup_stmt = select(CandidatePersona).where(
            CandidatePersona.user_account_id == user_uuid,
            func.lower(CandidatePersona.name) == clean_name.lower(),
            CandidatePersona.id != p_uuid,
        )
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"A persona with the name '{clean_name}' already exists "
                    "for this account."
                ),
            )

    # 3. Update fields (name only updated if not universal profile)
    if not persona.is_common_persona:
        persona.name = clean_name

    persona.headline = req.headline
    persona.target_roles = req.target_roles
    persona.target_industries = req.target_industries
    persona.seniority_level = req.seniority_level
    persona.years_experience = req.years_experience
    persona.min_salary = req.min_salary
    # Merge career_intelligence cleanly per top-level key to prevent accidental key wiping
    existing_ci = dict(persona.career_intelligence or {})
    incoming_ci = dict(req.career_intelligence or {})

    for k, v in incoming_ci.items():
        if k in ("contact_pii", "external_links", "profile_config") and isinstance(
            v, dict
        ):
            sub = dict(existing_ci.get(k) or {})
            sub.update(v)
            existing_ci[k] = sub
        else:
            existing_ci[k] = v
    ci = existing_ci
    c_pii = dict(ci.get("contact_pii") or {})

    target_full_name = (
        req.full_name.strip() if req.full_name and req.full_name.strip() else None
    ) or c_pii.get("full_name")
    target_email = (
        req.email.strip() if req.email and req.email.strip() else None
    ) or c_pii.get("email")
    target_phone = (
        req.phone.strip() if req.phone and req.phone.strip() else None
    ) or c_pii.get("phone")

    if target_full_name:
        c_pii["full_name"] = target_full_name
    if target_email:
        c_pii["email"] = target_email
    if target_phone:
        c_pii["phone"] = target_phone
    ci["contact_pii"] = c_pii
    persona.career_intelligence = ci

    # Synchronize project records into CVBlock (category="project")
    if "projects" in incoming_ci:
        current_project_fps: set[str] = set()
        for prj in ci.get("projects") or []:
            if not isinstance(prj, dict):
                continue
            p_name = str(prj.get("name") or "").strip()
            p_desc = str(prj.get("description") or "").strip()
            if not p_name or not p_desc:
                continue
            p_skills = list(prj.get("technologies") or [])
            if not p_skills:
                p_skills = extract_skills_from_text(f"{p_name} {p_desc}")
            p_metrics_list = extract_quantified_metrics(p_desc)
            p_metrics: dict[str, Any] = {
                str(m.metric_type): m.raw_metric for m in p_metrics_list
            }
            p_fp = prj.get("content_fingerprint") or compute_bullet_fingerprint(
                str(user_uuid), f"project:{p_name}", p_desc
            )
            current_project_fps.add(p_fp)

            b_stmt = select(CVBlock).where(
                CVBlock.user_account_id == user_uuid,
                CVBlock.content_fingerprint == p_fp,
            )
            existing_b = (await db.execute(b_stmt)).scalars().first()
            if existing_b:
                existing_b.title = p_name
                existing_b.content = p_desc
                existing_b.skills = p_skills
                existing_b.metrics = p_metrics
                block_to_link = existing_b
            else:
                embedding = await embed_text(p_desc)
                new_b = CVBlock(
                    id=uuid.uuid4(),
                    user_account_id=user_uuid,
                    user_profile_id=user_uuid,
                    category="project",
                    title=p_name,
                    organization="Independent / Open Source",
                    content=p_desc,
                    metrics=p_metrics,
                    skills=p_skills,
                    content_fingerprint=p_fp,
                    embedding=embedding,
                )
                db.add(new_b)
                block_to_link = new_b

            rel_stmt = select(PersonaCVBlockRel).where(
                PersonaCVBlockRel.persona_id == persona.id,
                PersonaCVBlockRel.cv_block_id == block_to_link.id,
            )
            if (await db.execute(rel_stmt)).scalars().first() is None:
                db.add(
                    PersonaCVBlockRel(
                        persona_id=persona.id,
                        cv_block_id=block_to_link.id,
                        priority_weight=1.0,
                        is_active=True,
                    )
                )

        del_b_stmt = select(CVBlock).where(
            CVBlock.user_account_id == user_uuid,
            CVBlock.category == "project",
        )
        user_proj_blocks = (await db.execute(del_b_stmt)).scalars().all()
        for upb in user_proj_blocks:
            if (
                upb.content_fingerprint
                and upb.content_fingerprint not in current_project_fps
            ):
                await db.execute(
                    delete(PersonaCVBlockRel).where(
                        PersonaCVBlockRel.cv_block_id == upb.id
                    )
                )
                await db.delete(upb)

    # Update account-level logistics and private PII if provided
    acc_stmt = select(UserAccount).where(UserAccount.id == user_uuid)
    acc_res = await db.execute(acc_stmt)
    user_acc = acc_res.scalar_one_or_none()
    if not user_acc:
        user_acc = await _get_or_create_account(db, user_uuid, current_user.email)

    if user_acc:
        if target_full_name:
            user_acc.full_name = target_full_name
        if target_phone is not None:
            user_acc.phone = target_phone
        if req.visa_status is not None:
            user_acc.visa_status = req.visa_status
        if req.preferred_locations is not None:
            user_acc.preferred_locations = req.preferred_locations
        if req.remote_preference is not None:
            user_acc.remote_preference = req.remote_preference

        # Safely update user_acc.email: check for duplicates across other accounts first
        if target_email and target_email.lower() != user_acc.email.lower():
            dup_acc_stmt = select(UserAccount.id).where(
                func.lower(UserAccount.email) == target_email.lower(),
                UserAccount.id != user_uuid,
            )
            has_dup = (await db.execute(dup_acc_stmt)).scalar_one_or_none()
            if not has_dup:
                user_acc.email = target_email
            else:
                logger.info(
                    "Contact email '%s' is registered to another account; stored in contact_pii only",
                    target_email,
                )

        # Also synchronize UserProfile for backward-compatibility
        u_prof = (
            (
                await db.execute(
                    select(UserProfile).where(
                        or_(
                            UserProfile.user_account_id == user_uuid,
                            UserProfile.id == user_uuid,
                        )
                    )
                )
            )
            .scalars()
            .first()
        )
        if u_prof:
            if target_full_name:
                u_prof.full_name = target_full_name
            if target_phone is not None:
                u_prof.phone = target_phone
            if target_email and target_email.lower() != u_prof.email.lower():
                dup_prof_stmt = select(UserProfile.id).where(
                    func.lower(UserProfile.email) == target_email.lower(),
                    UserProfile.id != u_prof.id,
                )
                has_dup_prof = (await db.execute(dup_prof_stmt)).scalar_one_or_none()
                if not has_dup_prof:
                    u_prof.email = target_email
            if req.visa_status is not None:
                u_prof.visa_status = req.visa_status
            if req.remote_preference is not None:
                u_prof.remote_preference = req.remote_preference

    # 2. Sync skills if provided
    if req.skills:
        existing_skills = {s.skill_name.lower(): s for s in (persona.skills or [])}
        for s in req.skills:
            s_clean = s.strip()
            if s_clean and s_clean.lower() not in existing_skills:
                new_skill = PersonaSkill(
                    id=uuid.uuid4(),
                    persona_id=persona.id,
                    skill_name=s_clean,
                    category="tool",
                    proficiency="intermediate",
                    years_experience=req.years_experience or 0,
                    is_core=True,
                )
                db.add(new_skill)

    await db.commit()
    await db.refresh(persona, attribute_names=["skills", "cv_block_rels"])

    acc_stmt = select(UserAccount).where(UserAccount.id == user_uuid)
    account = (await db.execute(acc_stmt)).scalar_one_or_none()

    return _build_persona_detail_response(persona, account=account)


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
    p_uuid = parse_uuid_or_400(persona_id, "persona_id")

    # Verify persona exists and belongs to user before modifying default state
    exists_stmt = select(CandidatePersona.id).where(
        CandidatePersona.id == p_uuid,
        CandidatePersona.user_account_id == user_uuid,
    )
    exists = (await db.execute(exists_stmt)).scalar_one_or_none()
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found or access denied.",
        )

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

    return {"status": "success", "default_persona_id": str(p_uuid)}


@router.delete(
    "/personas/{persona_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_persona(
    persona_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict[str, str]:
    """
    Delete a specialized candidate persona.

    Guards:
      - Universal Profile (is_common_persona = True) cannot be deleted.
      - If deleting the default persona, falls back to the Universal Profile.
    """
    user_uuid = _get_user_uuid(current_user)
    p_uuid = parse_uuid_or_400(persona_id, "persona_id")

    stmt = select(CandidatePersona).where(
        CandidatePersona.id == p_uuid,
        CandidatePersona.user_account_id == user_uuid,
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found or access denied.",
        )

    if persona.is_common_persona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The Universal Profile cannot be deleted.",
        )

    was_default = persona.is_default

    # Delete relational children
    await db.execute(delete(PersonaSkill).where(PersonaSkill.persona_id == p_uuid))
    await db.execute(
        delete(PersonaCVBlockRel).where(PersonaCVBlockRel.persona_id == p_uuid)
    )
    await db.execute(delete(JobMatchCache).where(JobMatchCache.persona_id == p_uuid))
    await db.execute(delete(CandidatePersona).where(CandidatePersona.id == p_uuid))

    # If deleted persona was default, designate Universal Persona as new default
    if was_default:
        await db.execute(
            update(CandidatePersona)
            .where(
                CandidatePersona.user_account_id == user_uuid,
                CandidatePersona.is_common_persona.is_(True),
            )
            .values(is_default=True)
        )

    await db.commit()
    return {"status": "deleted", "persona_id": persona_id}


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
    p_uuid = parse_uuid_or_400(persona_id, "persona_id")

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
        p_uuid = parse_uuid_or_400(persona_id, "persona_id")
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
            content_fingerprint=b.content_fingerprint,
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
    response: Response,
) -> CVBlockResponse:
    """
    Add a new master CV block and compute its vector embedding.
    Deduplicates against existing CVBlocks using content_fingerprint.
    """
    user_uuid = _get_user_uuid(current_user)
    account = await _get_or_create_account(db, user_uuid, current_user.email)

    comp_fp = req.content_fingerprint or compute_bullet_fingerprint(
        str(account.id), req.organization, req.content
    )

    # 1. Target persona resolution
    target_persona_uuids: list[uuid.UUID] = []
    if req.persona_ids:
        target_persona_uuids = [
            parse_uuid_or_400(pid, "persona_id") for pid in req.persona_ids
        ]
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

    # 2. Check for existing block with identical content fingerprint
    existing_stmt = select(CVBlock).where(
        CVBlock.user_account_id == account.id,
        CVBlock.content_fingerprint == comp_fp,
    )
    existing_block = (await db.execute(existing_stmt)).scalars().first()
    if existing_block:
        response.status_code = status.HTTP_200_OK
        if req.metrics:
            m_copy = dict(existing_block.metrics or {})
            m_copy.update(req.metrics)
            existing_block.metrics = m_copy
        if req.skills:
            s_copy = set(existing_block.skills or [])
            s_copy.update(req.skills)
            existing_block.skills = sorted(s_copy)

        for p_id in target_persona_uuids:
            rel_stmt = select(PersonaCVBlockRel).where(
                PersonaCVBlockRel.persona_id == p_id,
                PersonaCVBlockRel.cv_block_id == existing_block.id,
            )
            if (await db.execute(rel_stmt)).scalars().first() is None:
                db.add(
                    PersonaCVBlockRel(
                        persona_id=p_id,
                        cv_block_id=existing_block.id,
                        priority_weight=1.0,
                        is_active=True,
                    )
                )
        await db.commit()
        return CVBlockResponse(
            id=str(existing_block.id),
            category=existing_block.category,
            title=existing_block.title,
            organization=existing_block.organization,
            content=existing_block.content,
            metrics=dict(existing_block.metrics or {}),
            skills=list(existing_block.skills or []),
            content_fingerprint=existing_block.content_fingerprint,
            has_embedding=existing_block.embedding is not None,
        )

    # 3. New block: compute vector embedding and persist
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
        content_fingerprint=comp_fp,
        embedding=embedding,
    )
    db.add(block)

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
        content_fingerprint=block.content_fingerprint,
        has_embedding=True,
    )


@router.put(
    "/blocks/{block_id}",
    response_model=CVBlockResponse,
    status_code=status.HTTP_200_OK,
)
async def update_cv_block(
    block_id: str,
    req: CVBlockUpdateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CVBlockResponse:
    """
    Update an existing CV block and re-compute its vector embedding if content changed.
    """
    user_uuid = _get_user_uuid(current_user)
    account = await _get_or_create_account(db, user_uuid, current_user.email)
    b_uuid = parse_uuid_or_400(block_id, "block_id")

    stmt = select(CVBlock).where(
        CVBlock.id == b_uuid,
        CVBlock.user_account_id == account.id,
    )
    res = await db.execute(stmt)
    block = res.scalar_one_or_none()
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV block not found or access denied.",
        )

    if req.category is not None:
        block.category = req.category
    if req.title is not None:
        block.title = req.title
    if req.organization is not None:
        block.organization = req.organization
    if req.metrics is not None:
        block.metrics = req.metrics
    if req.skills is not None:
        block.skills = req.skills
    if req.content is not None and req.content.strip() != block.content:
        block.content = req.content
        block.embedding = await embed_text(req.content)

    block.content_fingerprint = compute_bullet_fingerprint(
        str(account.id), block.organization, block.content
    )

    await db.commit()
    await db.refresh(block)

    return CVBlockResponse(
        id=str(block.id),
        category=block.category,
        title=block.title,
        organization=block.organization,
        content=block.content,
        metrics=dict(block.metrics or {}),
        skills=list(block.skills or []),
        has_embedding=block.embedding is not None,
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
    b_uuid = parse_uuid_or_400(block_id, "block_id")

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
