"""
Unit tests for application tracker model and endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token
from app.models.application import Application
from app.models.user_profile import UserProfile


def test_application_model_instantiation() -> None:
    """Verify Application model can be instantiated with required fields."""
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    app = Application(
        user_profile_id=user_id,
        job_listing_id=job_id,
        status="saved",
        notes="Strong alignment with team vision.",
        custom_metadata={"salary_expectation": "$180k - $210k"},
    )

    assert app.user_profile_id == user_id
    assert app.job_listing_id == job_id
    assert app.status == "saved"
    assert app.notes == "Strong alignment with team vision."
    assert app.custom_metadata["salary_expectation"] == "$180k - $210k"


def test_application_relationships_declared() -> None:
    """Verify Application foreign keys to UserProfile and JobListing."""
    col_user = Application.user_profile_id.property.columns[0]
    col_job = Application.job_listing_id.property.columns[0]
    profile_fks = [fk.target_fullname for fk in col_user.foreign_keys]
    job_fks = [fk.target_fullname for fk in col_job.foreign_keys]

    assert "user_profile.id" in profile_fks
    assert "job_listing.id" in job_fks


@pytest.mark.asyncio
async def test_update_application_status_by_owner_succeeds(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify owner can update their own application status."""
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    app_id = uuid.uuid4()

    profile = UserProfile(
        id=user_id,
        full_name="Alice Owner",
        email=f"alice-{user_id}@example.com",
    )
    application = Application(
        id=app_id,
        user_profile_id=user_id,
        job_listing_id=job_id,
        status="saved",
    )
    db_session.add(profile)
    db_session.add(application)
    await db_session.commit()

    token = create_access_token(user_id=str(user_id))
    response = await async_client.patch(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "interviewing", "notes": "Passed screen."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(app_id)
    assert data["status"] == "interviewing"
    assert data["notes"] == "Passed screen."


@pytest.mark.asyncio
async def test_update_application_status_idor_rejected(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify User B cannot update User A's application (returns 404, no existence leak)."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    job_id = uuid.uuid4()
    app_id = uuid.uuid4()

    profile_a = UserProfile(
        id=user_a_id,
        full_name="Alice Owner",
        email=f"alice-{user_a_id}@example.com",
    )
    application = Application(
        id=app_id,
        user_profile_id=user_a_id,
        job_listing_id=job_id,
        status="saved",
    )
    db_session.add(profile_a)
    db_session.add(application)
    await db_session.commit()

    # User B attempts to patch User A's application
    token_b = create_access_token(user_id=str(user_b_id))
    response = await async_client.patch(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"status": "rejected"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found."
