"""
Authentication and account management REST API endpoints.

This module provides registration, authentication, and session identity endpoints:
  - ``POST /api/auth/register``: Register a candidate user account and provision
    its initial Universal / Common Persona (ADR-001).
  - ``POST /api/auth/login``: Authenticate via email & password and issue JWT token.
  - ``GET /api/auth/me``: Return current authenticated candidate profile and personas.
"""

import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import (
    DEFAULT_DEV_USER_ID,
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
)
from app.core.database import get_db
from app.models.user_account import CandidatePersona, UserAccount
from app.models.user_profile import UserProfile

logger = logging.getLogger("career_os.api.auth")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


class RegisterRequest(BaseModel):
    """
    Payload for candidate registration.
    """

    email: str = Field(..., examples=["candidate@example.com"])
    password: str = Field(..., min_length=8, examples=["SecurePass123!"])
    full_name: str = Field(..., examples=["Jane Doe"])
    visa_status: str = Field(
        default="None",
        examples=["Citizen", "H-1B", "F-1 OPT", "None"],
    )
    citizenship_country_code: str | None = Field(default=None, examples=["US", "IN"])
    preferred_locations: list[str] = Field(
        default_factory=list,
        examples=[["San Francisco, CA", "Remote"]],
    )
    remote_preference: str = Field(default="Remote", examples=["Remote", "Hybrid"])


class LoginRequest(BaseModel):
    """
    Payload for user authentication.
    """

    email: str = Field(..., examples=["candidate@example.com"])
    password: str = Field(..., examples=["SecurePass123!"])


class PersonaSummaryResponse(BaseModel):
    """
    Summary view of a candidate persona.
    """

    id: str
    name: str
    is_common_persona: bool
    headline: str | None
    seniority_level: str
    years_experience: int
    target_roles: list[str]
    is_default: bool


class UserAccountResponse(BaseModel):
    """
    Full candidate user account response with associated personas.
    """

    id: str
    email: str
    full_name: str
    visa_status: str
    citizenship_country_code: str | None
    preferred_locations: list[str]
    remote_preference: str
    is_active: bool
    created_at: datetime
    personas: list[PersonaSummaryResponse]


class AuthResponse(BaseModel):
    """
    Authentication success response with access token and initial persona.
    """

    access_token: str
    token_type: str = "bearer"
    user: UserAccountResponse
    default_persona_id: str


def _serialize_persona(persona: CandidatePersona) -> PersonaSummaryResponse:
    return PersonaSummaryResponse(
        id=str(persona.id),
        name=persona.name,
        is_common_persona=persona.is_common_persona,
        headline=persona.headline,
        seniority_level=persona.seniority_level,
        years_experience=persona.years_experience,
        target_roles=list(persona.target_roles or []),
        is_default=persona.is_default,
    )


def _serialize_user(user: UserAccount) -> UserAccountResponse:
    return UserAccountResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        visa_status=user.visa_status,
        citizenship_country_code=user.citizenship_country_code,
        preferred_locations=list(user.preferred_locations or []),
        remote_preference=user.remote_preference,
        is_active=user.is_active,
        created_at=user.created_at,
        personas=[_serialize_persona(p) for p in (user.personas or [])],
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_account(
    req: RegisterRequest,
    db: DatabaseSession,
) -> AuthResponse:
    """
    Register a new candidate user account and provision the Universal Persona.
    """
    normalized_email = req.email.strip().lower()

    # Check for existing email registration
    existing_stmt = select(UserAccount).where(UserAccount.email == normalized_email)
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash cleartext password securely
    hashed_pw = hash_password(req.password)

    # Create root user account
    account_id = uuid.uuid4()
    account = UserAccount(
        id=account_id,
        email=normalized_email,
        password_hash=hashed_pw,
        full_name=req.full_name.strip(),
        visa_status=req.visa_status,
        citizenship_country_code=req.citizenship_country_code,
        preferred_locations=req.preferred_locations,
        remote_preference=req.remote_preference,
        is_active=True,
    )
    db.add(account)

    # Automatically provision the Universal / Common Persona (ADR-001)
    universal_persona_id = uuid.uuid4()
    universal_persona = CandidatePersona(
        id=universal_persona_id,
        user_account_id=account_id,
        name="Universal Profile",
        is_common_persona=True,
        headline=f"{req.full_name.strip()} — Full Professional Profile",
        target_roles=[],
        target_industries=[],
        years_experience=0,
        seniority_level="mid",
        is_default=True,
    )
    db.add(universal_persona)

    # Also provision a linked UserProfile for legacy agent continuity
    legacy_profile = UserProfile(
        id=account_id,
        user_account_id=account_id,
        email=normalized_email,
        full_name=req.full_name.strip(),
        visa_status=req.visa_status,
        remote_preference=req.remote_preference,
        tone_directives={},
        target_roles=[],
        target_locations=req.preferred_locations,
    )
    db.add(legacy_profile)

    await db.flush()
    await db.refresh(account, attribute_names=["personas"])

    token = create_access_token(
        user_id=str(account.id),
        email=account.email,
        role="candidate",
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_serialize_user(account),
        default_persona_id=str(universal_persona_id),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
)
async def login_account(
    req: LoginRequest,
    db: DatabaseSession,
) -> AuthResponse:
    """
    Authenticate candidate credentials and issue a signed JWT access token.
    """
    normalized_email = req.email.strip().lower()

    stmt = (
        select(UserAccount)
        .options(selectinload(UserAccount.personas))
        .where(UserAccount.email == normalized_email)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account is None or not verify_password(
        req.password, account.password_hash or ""
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated.",
        )

    # Resolve default persona
    default_persona_id = str(account.id)
    if account.personas:
        default_p = next(
            (p for p in account.personas if p.is_default),
            next(
                (p for p in account.personas if p.is_common_persona),
                account.personas[0],
            ),
        )
        default_persona_id = str(default_p.id)

    token = create_access_token(
        user_id=str(account.id),
        email=account.email,
        role="candidate",
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_serialize_user(account),
        default_persona_id=default_persona_id,
    )


@router.get(
    "/me",
    response_model=UserAccountResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_profile(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> UserAccountResponse:
    """
    Retrieve candidate profile and personas for the current authenticated principal.
    """
    try:
        user_uuid = uuid.UUID(current_user.user_id)
    except ValueError:
        user_uuid = uuid.UUID(DEFAULT_DEV_USER_ID)

    stmt = (
        select(UserAccount)
        .options(selectinload(UserAccount.personas))
        .where(UserAccount.id == user_uuid)
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()

    if account is None:
        # Dev fallback: instantiate and return temporary developer context
        mock_persona = PersonaSummaryResponse(
            id=str(uuid.uuid4()),
            name="Universal Profile (Dev)",
            is_common_persona=True,
            headline="Developer Sandbox Profile",
            seniority_level="senior",
            years_experience=5,
            target_roles=["Senior Software Engineer"],
            is_default=True,
        )
        return UserAccountResponse(
            id=str(user_uuid),
            email=current_user.email or "developer@career-os.local",
            full_name="Career-OS Developer",
            visa_status="Citizen",
            citizenship_country_code="US",
            preferred_locations=["San Francisco, CA", "Remote"],
            remote_preference="Remote",
            is_active=True,
            created_at=datetime.utcnow(),
            personas=[mock_persona],
        )

    return _serialize_user(account)
