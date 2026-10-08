"""
SQLAlchemy ORM model declarations for long-term relational persistence.

Each model maps one PostgreSQL table (singular naming: user_profile, job_listing,
cv_block, company_dossier, feedback_log). Models contain only schema definitions
and relationship declarations — no business logic, no LLM calls. The separation
guarantees that the data layer can be migrated independently via Alembic without
touching agent or API code.
"""

from app.models.application import Application
from app.models.base import Base
from app.models.company_dossier import CompanyDossier
from app.models.cv_block import CVBlock
from app.models.feedback_log import FeedbackLog
from app.models.ingestion import (
    ATSBoard,
    IngestionRun,
    IngestionTask,
    ProviderState,
    ProviderUsage,
)
from app.models.job_listing import JobListing
from app.models.user_profile import UserProfile

__all__ = [
    "ATSBoard",
    "Application",
    "Base",
    "CompanyDossier",
    "CVBlock",
    "FeedbackLog",
    "IngestionRun",
    "IngestionTask",
    "JobListing",
    "ProviderState",
    "ProviderUsage",
    "UserProfile",
]
