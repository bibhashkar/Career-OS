"""
Backfill script to populate job_listing.ats_requirements for existing jobs.

Extracts:
- required_skills & preferred_skills
- min_experience_years
- seniority_level
- functional_family
- education_level
- industry_vertical & domain_strictness
- visa_sponsorship
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import get_session_context
from app.ingestion.deterministic_extractor import (
    extract_deterministic_requirements,
)
from app.models.job_listing import JobListing
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("backfill_ats_requirements")


async def backfill() -> None:
    logger.info("Starting ATS requirements backfill...")
    count = 0
    updated = 0

    async with get_session_context() as session:
        stmt = select(JobListing)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        logger.info("Found %d total job listings to check.", len(jobs))

        for job in jobs:
            count += 1
            ats_reqs = job.ats_requirements or {}
            # Needs backfill if empty or missing required_skills
            if (
                not ats_reqs
                or not ats_reqs.get("required_skills")
                or "functional_family" not in ats_reqs
            ):
                reqs = extract_deterministic_requirements(
                    title=job.title,
                    raw_description=job.raw_description,
                    company_name=job.company_name,
                )
                job.ats_requirements = reqs.model_dump()
                if not job.industry_vertical or job.industry_vertical == "general_saas":
                    job.industry_vertical = reqs.industry_vertical
                job.domain_strictness = reqs.domain_strictness
                if (
                    not job.visa_sponsorship or job.visa_sponsorship == "unknown"
                ) and reqs.visa_sponsorship.value != "unknown":
                    job.visa_sponsorship = str(reqs.visa_sponsorship.value)
                updated += 1
                if updated % 20 == 0:
                    await session.flush()
                    logger.info(
                        "Progress: %d / %d jobs backfilled.", updated, len(jobs)
                    )

        await session.commit()
        logger.info("Completed backfill: %d / %d jobs updated.", updated, count)


if __name__ == "__main__":
    asyncio.run(backfill())
