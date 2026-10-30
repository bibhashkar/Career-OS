"""
Standalone database migration and deduplication script.

Executes the following operations:
1. Ensures schema columns `canonical_fingerprint` and `location_postings` exist.
2. Identifies and merges duplicate jobs (both exact fingerprint matches and multi-location variants).
3. Elects the best canonical record per requisition using primary scoring.
4. Consolidates all regional URLs and locations into `location_postings` on the canonical record.
5. Re-points or clears referencing `job_match_cache` entries.
6. Prunes redundant rows and enforces unique indexing on `fingerprint`.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.ingestion.service import (
    compute_canonical_fingerprint,
    compute_dedupe_fingerprint,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("career_os.scripts.dedupe_jobs")


async def migrate_and_dedupe() -> None:
    async with async_session_maker() as session:
        logger.info("Step 1: Ensuring schema columns and indexes exist...")
        await session.execute(
            text(
                """
                ALTER TABLE job_listing 
                ADD COLUMN IF NOT EXISTS canonical_fingerprint VARCHAR(64);
                
                ALTER TABLE job_listing 
                ADD COLUMN IF NOT EXISTS location_postings JSONB DEFAULT '[]'::jsonb NOT NULL;
                """
            )
        )
        await session.commit()

        logger.info("Step 2: Fetching all active job listings...")
        res = await session.execute(
            text(
                """
                SELECT id, company_name, title, raw_location, country_code, state_province_code,
                       city, salary_range, salary_min, salary_max, source_job_id, apply_url, 
                       fingerprint, canonical_fingerprint, location_postings, ats_requirements, 
                       remote_scope, posted_at, created_at, first_seen_at
                FROM job_listing
                ORDER BY created_at ASC;
                """
            )
        )
        rows = res.mappings().all()
        logger.info("Loaded %d total job listings.", len(rows))

        # Group listings by canonical_fingerprint
        grouped_jobs: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            c_fp = r["canonical_fingerprint"]
            if not c_fp:
                c_fp = compute_canonical_fingerprint(r["company_name"], r["title"])
            grouped_jobs.setdefault(c_fp, []).append(dict(r))

        logger.info(
            "Discovered %d unique canonical requisition clusters.", len(grouped_jobs)
        )

        duplicate_clusters = {k: v for k, v in grouped_jobs.items() if len(v) > 1}
        logger.info(
            "Found %d clusters containing duplicate/variant listings (affecting %d total rows).",
            len(duplicate_clusters),
            sum(len(v) for v in duplicate_clusters.values()),
        )

        canonical_updates: list[dict[str, Any]] = []
        rows_to_delete: list[str] = []

        for c_fp, group in grouped_jobs.items():
            if len(group) == 1:
                item = group[0]
                postings = item.get("location_postings") or []
                if not postings:
                    postings = [
                        {
                            "location": item["raw_location"],
                            "city": item["city"],
                            "state_code": item["state_province_code"],
                            "country_code": item["country_code"],
                            "salary_range": item["salary_range"],
                            "source_job_id": item["source_job_id"],
                            "apply_url": item["apply_url"],
                            "is_primary": True,
                        }
                    ]
                fp = item["fingerprint"] or compute_dedupe_fingerprint(
                    item["company_name"], item["title"], item["raw_location"]
                )
                canonical_updates.append(
                    {
                        "id": item["id"],
                        "fingerprint": fp,
                        "canonical_fingerprint": c_fp,
                        "raw_location": item["raw_location"],
                        "location_postings": postings,
                    }
                )
                continue

            # Multi-job cluster: Score each to elect primary
            def _score_item(it: dict[str, Any]) -> float:
                score = 0.0
                if (
                    it.get("salary_min")
                    or it.get("salary_max")
                    or it.get("salary_range")
                ):
                    score += 20.0
                if it.get("ats_requirements") and it["ats_requirements"].get(
                    "required_skills"
                ):
                    score += 10.0
                if it.get("remote_scope") in ("worldwide_global", "country_wide"):
                    score += 10.0
                ts = (
                    it.get("posted_at")
                    or it.get("first_seen_at")
                    or it.get("created_at")
                )
                if ts:
                    # Prefer earlier original requisition
                    if isinstance(ts, str):
                        try:
                            ts = datetime.fromisoformat(ts)
                        except Exception:
                            ts = None
                    if ts:
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                        age = (datetime.now(UTC) - ts).days
                        score += min(20.0, max(0.0, age * 0.2))
                return score

            sorted_group = sorted(group, key=_score_item, reverse=True)
            primary = sorted_group[0]
            non_primaries = sorted_group[1:]

            # Consolidate all location postings
            consolidated_postings: list[dict[str, Any]] = []
            distinct_locations: list[str] = []

            for idx, member in enumerate(sorted_group):
                loc = member["raw_location"] or "Remote"
                if loc not in distinct_locations:
                    distinct_locations.append(loc)
                consolidated_postings.append(
                    {
                        "location": loc,
                        "city": member["city"],
                        "state_code": member["state_province_code"],
                        "country_code": member["country_code"],
                        "salary_range": member["salary_range"],
                        "source_job_id": member["source_job_id"],
                        "apply_url": member["apply_url"],
                        "is_primary": (idx == 0),
                    }
                )

            # Consolidate raw_location display string
            consolidated_loc = ", ".join(distinct_locations[:4])
            if len(distinct_locations) > 4:
                consolidated_loc += f" (+{len(distinct_locations) - 4} others)"

            fp = primary["fingerprint"] or compute_dedupe_fingerprint(
                primary["company_name"], primary["title"], primary["raw_location"]
            )

            canonical_updates.append(
                {
                    "id": primary["id"],
                    "fingerprint": fp,
                    "canonical_fingerprint": c_fp,
                    "raw_location": consolidated_loc,
                    "location_postings": consolidated_postings,
                }
            )

            for non_pri in non_primaries:
                rows_to_delete.append(str(non_pri["id"]))

        logger.info(
            "Prepared %d canonical updates and marked %d duplicate rows for safe pruning.",
            len(canonical_updates),
            len(rows_to_delete),
        )

        # Step 3: Handle referencing tables (job_match_cache)
        logger.info("Step 3: Flushing obsolete job_match_cache entries...")
        await session.execute(text("DELETE FROM job_match_cache;"))
        await session.commit()

        # Step 4: Batch delete duplicate job_listing rows
        logger.info("Step 4: Pruning %d duplicate rows...", len(rows_to_delete))
        batch_size = 500
        for i in range(0, len(rows_to_delete), batch_size):
            chunk = rows_to_delete[i : i + batch_size]
            formatted_ids = ", ".join(f"'{jid}'" for jid in chunk)
            await session.execute(
                text(f"DELETE FROM job_listing WHERE id IN ({formatted_ids});")
            )
            await session.commit()
            logger.info("Deleted batch %d to %d.", i, i + len(chunk))

        # Step 5: Batch update canonical job listings
        logger.info("Step 5: Updating %d canonical records...", len(canonical_updates))
        for i in range(0, len(canonical_updates), batch_size):
            update_chunk = canonical_updates[i : i + batch_size]
            for u in update_chunk:
                await session.execute(
                    text(
                        """
                        UPDATE job_listing 
                        SET fingerprint = :fp,
                            canonical_fingerprint = :c_fp,
                            raw_location = :loc,
                            location_postings = CAST(:postings AS JSONB)
                        WHERE id = :id;
                        """
                    ),
                    {
                        "id": u["id"],
                        "fp": u["fingerprint"],
                        "c_fp": u["canonical_fingerprint"],
                        "loc": u["raw_location"],
                        "postings": json.dumps(u["location_postings"]),
                    },
                )
            await session.commit()
            logger.info("Updated canonical batch %d to %d.", i, i + len(update_chunk))

        # Step 6: Create Unique and Performance Indexes
        logger.info("Step 6: Enforcing database constraints...")
        await session.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_job_listing_fingerprint 
                ON job_listing(fingerprint) 
                WHERE fingerprint IS NOT NULL;

                CREATE INDEX IF NOT EXISTS idx_job_listing_canonical_fingerprint 
                ON job_listing(canonical_fingerprint);
                """
            )
        )
        await session.commit()

        # Step 7: Final verification
        final_count = (
            await session.execute(text("SELECT count(*) FROM job_listing;"))
        ).scalar_one()
        final_dups = (
            await session.execute(
                text(
                    """
                    SELECT count(*) FROM (
                        SELECT canonical_fingerprint, count(*) 
                        FROM job_listing 
                        GROUP BY canonical_fingerprint 
                        HAVING count(*) > 1
                    ) s;
                    """
                )
            )
        ).scalar_one()

        logger.info(
            "MIGRATION COMPLETE! Final listings count: %d. Remaining duplicate clusters: %d.",
            final_count,
            final_dups,
        )


if __name__ == "__main__":
    asyncio.run(migrate_and_dedupe())
