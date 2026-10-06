"""
Unit tests for application tracker model and endpoints.
"""

import uuid

from app.models.application import Application


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
