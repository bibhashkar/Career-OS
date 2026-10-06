"""
Application tracker API endpoints.

Enables candidates to save job listings and track the full application
lifecycle (saved -> applied -> interviewing -> offered -> rejected).
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.database import get_db
from app.models.application import Application
from app.models.job_listing import JobListing
from app.models.user_profile import UserProfile

router = APIRouter(prefix="/api/applications", tags=["Applications"])

VALID_STATUSES = {"saved", "applied", "interviewing", "offered", "rejected"}
DbSession = Annotated[AsyncSession, Depends(get_db)]


class ApplicationCreateRequest(BaseModel):
    """Payload to create or update an application tracking record."""

    job_listing_id: str = Field(..., description="Target JobListing UUID.")
    status: str = Field(
        "saved",
        description="Application status: saved, applied, etc.",
    )
    notes: str | None = Field(None, description="Candidate notes or interview log.")
    custom_metadata: dict[str, Any] = Field(default_factory=dict)


class ApplicationResponse(BaseModel):
    """Application record response payload."""

    id: str
    user_profile_id: str
    job_listing_id: str
    status: str
    notes: str | None
    custom_metadata: dict[str, Any]
    job_title: str | None = None
    company_name: str | None = None
    created_at: str | None = None


class ApplicationStatusUpdateRequest(BaseModel):
    """Payload to transition application status."""

    status: str = Field(
        ...,
        description="New status ('saved', 'applied', etc.).",
    )
    notes: str | None = Field(None)


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    user: CurrentUser,
    db: DbSession,
    status_filter: str | None = None,
) -> list[ApplicationResponse]:
    """List tracked applications for the authenticated candidate."""
    try:
        user_uuid = uuid.UUID(user.user_id)
    except ValueError:
        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    query = (
        select(Application, JobListing.title, JobListing.company_name)
        .outerjoin(JobListing, Application.job_listing_id == JobListing.id)
        .where(Application.user_profile_id == user_uuid)
    )

    if status_filter and status_filter in VALID_STATUSES:
        query = query.where(Application.status == status_filter)

    result = await db.execute(query)
    rows = result.all()

    return [
        ApplicationResponse(
            id=str(app.id),
            user_profile_id=str(app.user_profile_id),
            job_listing_id=str(app.job_listing_id),
            status=app.status,
            notes=app.notes,
            custom_metadata=app.custom_metadata or {},
            job_title=job_title,
            company_name=company_name,
            created_at=app.created_at.isoformat() if app.created_at else None,
        )
        for app, job_title, company_name in rows
    ]


@router.post(
    "", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_or_update_application(
    request: ApplicationCreateRequest,
    user: CurrentUser,
    db: DbSession,
) -> ApplicationResponse:
    """Save a job listing to tracker or update its application state."""
    if request.status not in VALID_STATUSES:
        valid_list = sorted(VALID_STATUSES)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{request.status}'. Allowed: {valid_list}",
        )

    try:
        job_uuid = uuid.UUID(request.job_listing_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid job_listing_id UUID format.",
        ) from err

    # Ensure target job listing exists
    job_result = await db.execute(select(JobListing).where(JobListing.id == job_uuid))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job listing not found.",
        )

    # Resolve candidate profile or create demo profile
    try:
        user_uuid = uuid.UUID(user.user_id)
    except ValueError:
        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_uuid)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        user_email = user.email or f"{user.user_id}@career-os.local"
        user_name = user_email.split("@")[0].capitalize()
        profile = UserProfile(
            id=user_uuid,
            full_name=user_name,
            email=user_email,
        )
        db.add(profile)
        await db.flush()

    # Check for existing application record
    app_result = await db.execute(
        select(Application).where(
            Application.user_profile_id == user_uuid,
            Application.job_listing_id == job_uuid,
        )
    )
    existing_app = app_result.scalar_one_or_none()

    if existing_app:
        existing_app.status = request.status
        if request.notes is not None:
            existing_app.notes = request.notes
        if request.custom_metadata:
            existing_app.custom_metadata = {
                **(existing_app.custom_metadata or {}),
                **request.custom_metadata,
            }
        app_record = existing_app
    else:
        app_record = Application(
            user_profile_id=user_uuid,
            job_listing_id=job_uuid,
            status=request.status,
            notes=request.notes,
            custom_metadata=request.custom_metadata,
        )
        db.add(app_record)

    await db.flush()

    return ApplicationResponse(
        id=str(app_record.id),
        user_profile_id=str(app_record.user_profile_id),
        job_listing_id=str(app_record.job_listing_id),
        status=app_record.status,
        notes=app_record.notes,
        custom_metadata=app_record.custom_metadata or {},
        job_title=job.title,
        company_name=job.company_name,
        created_at=app_record.created_at.isoformat() if app_record.created_at else None,
    )


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: str,
    request: ApplicationStatusUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> ApplicationResponse:
    """Transition an existing application's stage."""
    if request.status not in VALID_STATUSES:
        valid_list = sorted(VALID_STATUSES)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{request.status}'. Allowed: {valid_list}",
        )

    try:
        app_uuid = uuid.UUID(application_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid application UUID format.",
        ) from err

    query = (
        select(Application, JobListing.title, JobListing.company_name)
        .outerjoin(JobListing, Application.job_listing_id == JobListing.id)
        .where(Application.id == app_uuid)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    app_record, job_title, company_name = row
    app_record.status = request.status
    if request.notes is not None:
        app_record.notes = request.notes

    await db.flush()

    return ApplicationResponse(
        id=str(app_record.id),
        user_profile_id=str(app_record.user_profile_id),
        job_listing_id=str(app_record.job_listing_id),
        status=app_record.status,
        notes=app_record.notes,
        custom_metadata=app_record.custom_metadata or {},
        job_title=job_title,
        company_name=company_name,
        created_at=app_record.created_at.isoformat() if app_record.created_at else None,
    )
