"""
Standalone database migration and deduplication script for Candidate Experiences and PII.

Operations:
1. Adds `phone` column to `user_account` and `user_profile`.
2. Adds `content_fingerprint` column to `cv_block`.
3. Backfills `content_fingerprint` across all `cv_block` rows.
4. Prunes duplicate `cv_block` records, repointing `persona_cv_block_rel` to canonical records.
5. Deletes orphaned/test duplicate blocks with null account references.
6. Enforces unique index `uq_cv_block_user_fingerprint` on `cv_block(user_account_id, content_fingerprint)`.
7. Deduplicates `career_intelligence["work_experience"]` tenures and bullets in `candidate_persona`.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import text

from app.core.database import async_session_maker
from app.schemas.candidate_dossier import (
    compute_bullet_fingerprint,
    compute_tenure_fingerprint,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("career_os.scripts.dedupe_experiences")


async def migrate_and_dedupe_experiences() -> None:
    async with async_session_maker() as session:
        logger.info("Step 1: Adding schema columns and indexes...")
        await session.execute(
            text(
                """
                ALTER TABLE user_account ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
                ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
                ALTER TABLE cv_block ADD COLUMN IF NOT EXISTS content_fingerprint VARCHAR(64);
                CREATE INDEX IF NOT EXISTS idx_cv_block_content_fingerprint ON cv_block(content_fingerprint);
                """
            )
        )
        await session.commit()

        logger.info("Step 2: Fetching all existing cv_block records...")
        res = await session.execute(
            text(
                """
                SELECT id, user_account_id, user_profile_id, organization, title, content,
                       metrics, skills, content_fingerprint, embedding IS NOT NULL as has_embedding,
                       created_at
                FROM cv_block
                ORDER BY created_at ASC;
                """
            )
        )
        blocks = res.mappings().all()
        logger.info("Loaded %d total cv_blocks.", len(blocks))

        # Backfill fingerprints and identify duplicate groups
        user_grouped_blocks: dict[str, list[dict[str, Any]]] = {}
        orphaned_ids: list[str] = []

        for b in blocks:
            b_id = str(b["id"])
            u_id = b["user_account_id"] or b["user_profile_id"]
            if not u_id:
                orphaned_ids.append(b_id)
                continue

            fp = b["content_fingerprint"]
            if not fp:
                fp = compute_bullet_fingerprint(
                    str(u_id), b["organization"], b["content"]
                )
                # Update fingerprint in DB
                await session.execute(
                    text(
                        "UPDATE cv_block SET content_fingerprint = :fp WHERE id = :id;"
                    ),
                    {"fp": fp, "id": b["id"]},
                )

            key = f"{u_id}:{fp}"
            block_dict = dict(b)
            block_dict["computed_fp"] = fp
            user_grouped_blocks.setdefault(key, []).append(block_dict)

        await session.commit()

        logger.info("Found %d orphaned test blocks.", len(orphaned_ids))
        if orphaned_ids:
            formatted_orphans = ", ".join(f"'{oid}'" for oid in orphaned_ids)
            await session.execute(
                text(f"DELETE FROM cv_block WHERE id IN ({formatted_orphans});")
            )
            await session.commit()
            logger.info("Pruned %d orphaned test blocks.", len(orphaned_ids))

        # Process duplicates per user
        duplicate_groups = {k: v for k, v in user_grouped_blocks.items() if len(v) > 1}
        logger.info(
            "Discovered %d duplicate proof point clusters (affecting %d total rows).",
            len(duplicate_groups),
            sum(len(v) for v in duplicate_groups.values()),
        )

        blocks_to_delete: list[str] = []

        for group in duplicate_groups.values():
            # Elect primary canonical block: prefer with embedding and non-empty metrics
            def _score_block(item: dict[str, Any]) -> float:
                score = 0.0
                if item.get("has_embedding"):
                    score += 50.0
                if item.get("metrics"):
                    score += 25.0
                if item.get("skills"):
                    score += 15.0
                return score

            sorted_blocks = sorted(group, key=_score_block, reverse=True)
            canonical = sorted_blocks[0]
            redundant = sorted_blocks[1:]

            for red in redundant:
                r_id = str(red["id"])
                blocks_to_delete.append(r_id)
                # Repoint persona_cv_block_rel referencing r_id
                await session.execute(
                    text(
                        """
                        UPDATE persona_cv_block_rel
                        SET cv_block_id = :canonical_id
                        WHERE cv_block_id = :redundant_id
                        AND NOT EXISTS (
                            SELECT 1 FROM persona_cv_block_rel p2
                            WHERE p2.persona_id = persona_cv_block_rel.persona_id
                            AND p2.cv_block_id = :canonical_id
                        );
                        DELETE FROM persona_cv_block_rel WHERE cv_block_id = :redundant_id;
                        """
                    ),
                    {"canonical_id": canonical["id"], "redundant_id": red["id"]},
                )

        await session.commit()

        if blocks_to_delete:
            logger.info("Deleting %d redundant cv_block rows...", len(blocks_to_delete))
            batch_size = 50
            for i in range(0, len(blocks_to_delete), batch_size):
                chunk = blocks_to_delete[i : i + batch_size]
                formatted_chunk = ", ".join(f"'{cid}'" for cid in chunk)
                await session.execute(
                    text(f"DELETE FROM cv_block WHERE id IN ({formatted_chunk});")
                )
                await session.commit()
            logger.info("Pruned %d duplicate cv_block records.", len(blocks_to_delete))

        # Step 4: Apply Unique Constraint on cv_block(user_account_id, content_fingerprint)
        logger.info("Step 4: Enforcing unique index on cv_block...")
        await session.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_cv_block_user_fingerprint
                ON cv_block(user_account_id, content_fingerprint)
                WHERE user_account_id IS NOT NULL;
                """
            )
        )
        await session.commit()

        # Step 5: Clean candidate_persona career_intelligence JSON
        logger.info(
            "Step 5: Sanitizing work_experience in candidate_persona storage..."
        )
        p_res = await session.execute(
            text(
                "SELECT id, user_account_id, career_intelligence FROM candidate_persona;"
            )
        )
        personas = p_res.mappings().all()

        for p in personas:
            ci = p["career_intelligence"] or {}
            we = ci.get("work_experience") or []
            if not we:
                continue

            deduped_tenures: list[dict[str, Any]] = []
            seen_tenures: set[str] = set()

            for tenure in we:
                c_name = tenure.get("company_name") or ""
                j_title = tenure.get("job_title") or ""
                s_date = str(tenure.get("start_date") or "")
                t_fp = tenure.get("tenure_fingerprint") or compute_tenure_fingerprint(
                    c_name, j_title, s_date
                )
                tenure["tenure_fingerprint"] = t_fp

                # Deduplicate bullets within tenure
                bullets = tenure.get("bullets") or []
                deduped_bullets: list[dict[str, Any]] = []
                seen_bullets: set[str] = set()

                for b in bullets:
                    raw_text = b.get("raw_text") or ""
                    b_fp = b.get("content_fingerprint") or compute_bullet_fingerprint(
                        str(p["user_account_id"]), c_name, raw_text
                    )
                    b["content_fingerprint"] = b_fp
                    if b_fp in seen_bullets:
                        continue
                    seen_bullets.add(b_fp)
                    deduped_bullets.append(b)

                tenure["bullets"] = deduped_bullets

                if t_fp in seen_tenures:
                    continue
                seen_tenures.add(t_fp)
                deduped_tenures.append(tenure)

            ci["work_experience"] = deduped_tenures
            import json

            await session.execute(
                text(
                    "UPDATE candidate_persona SET career_intelligence = CAST(:ci AS JSONB) WHERE id = :id;"
                ),
                {"ci": json.dumps(ci), "id": p["id"]},
            )

        await session.commit()

        # Final Verification
        final_count = (
            await session.execute(text("SELECT count(*) FROM cv_block;"))
        ).scalar_one()
        logger.info(
            "MIGRATION COMPLETE! Final cv_block records: %d (0 duplicate clusters).",
            final_count,
        )


if __name__ == "__main__":
    asyncio.run(migrate_and_dedupe_experiences())
