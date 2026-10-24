"""
Administrator seed and bootstrap service.

Ensures that the Career-OS environment always has an initial administrative account
matching settings.ADMIN_EMAIL, enabling immediate administrative observability and
control plane operation upon initial container deployment or developer startup.
"""

import logging
import uuid

from sqlalchemy import select

from app.core.auth import hash_password
from app.core.config import settings
from app.core.database import async_session_maker
from app.models.user_account import CandidatePersona, UserAccount
from app.models.user_profile import UserProfile

logger = logging.getLogger("career_os.core.admin_seed")


async def ensure_default_admin() -> None:
    """
    Ensure the root administrator account exists in the PostgreSQL database.

    Idempotent operation:
      - If an account exists with settings.ADMIN_EMAIL, ensures its role is 'admin'.
      - If no account exists, creates the root administrator UserAccount,
        associated Universal CandidatePersona, and legacy UserProfile.
    """
    admin_email = settings.ADMIN_EMAIL.strip().lower()

    async with async_session_maker() as db:
        try:
            stmt = select(UserAccount).where(UserAccount.email == admin_email)
            result = await db.execute(stmt)
            account = result.scalar_one_or_none()

            if account is not None:
                if account.role != "admin":
                    account.role = "admin"
                    await db.commit()
                    logger.info(
                        "Upgraded existing user %s to 'admin' role", admin_email
                    )
                return

            account_id = uuid.uuid4()
            admin_user = UserAccount(
                id=account_id,
                email=admin_email,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                full_name=settings.ADMIN_FULL_NAME,
                role="admin",
                visa_status="Citizen",
                preferred_locations=["Remote"],
                remote_preference="Remote",
                is_active=True,
            )
            db.add(admin_user)

            persona_id = uuid.uuid4()
            persona = CandidatePersona(
                id=persona_id,
                user_account_id=account_id,
                name="Admin Profile",
                is_common_persona=True,
                headline="Platform Administrator",
                target_roles=["Administrator"],
                target_industries=[],
                years_experience=10,
                seniority_level="staff",
                is_default=True,
            )
            db.add(persona)

            legacy_profile = UserProfile(
                id=account_id,
                user_account_id=account_id,
                email=admin_email,
                full_name=settings.ADMIN_FULL_NAME,
                visa_status="Citizen",
                remote_preference="Remote",
                tone_directives={},
                target_roles=["Administrator"],
                target_locations=[],
            )
            db.add(legacy_profile)

            await db.commit()
            logger.info(
                "Successfully provisioned default administrator account: %s",
                admin_email,
            )
        except Exception as exc:
            await db.rollback()
            logger.warning(
                "Default administrator account provisioning deferred during startup: %s",
                exc,
            )
