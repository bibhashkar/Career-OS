#!/usr/bin/env python3
"""
Career-OS Multi-Board Job Crawler & Ingestion CLI.

Scalable ingestion engine managing 1,000+ employer career portals across
global technology hubs (US, Canada, UK, Europe, Australia, New Zealand) and
specialized sectors (HFT/Quant, FinTech, HealthTech, AI/ML, DevOps, Cybersecurity).

Capabilities:
  1. Seed Database (--seed-db): Loads declarative catalog from data/seed_boards.yaml
     into the ats_board table with strict foreign key integrity.
  2. Targeted Sector Crawling (--industry): Crawls all boards for a sector
     (e.g. hft_quant_trading, fintech, healthtech, ai_machine_learning).
  3. Regional Filtering (--country, --region): Crawls by geographic hub.
  4. SLA Due Scheduler (--due): Crawls boards past their next_sync_at timestamp.
  5. Multi-Dimensional Statistics (--stats): Real-time breakdown of active jobs
     by sector, country, workplace modality, and visa sponsorship status.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from sqlalchemy import func, select

# Add backend directory to sys.path so app imports resolve
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
sys.path.insert(0, str(_BACKEND_DIR))

from app.core.database import get_session_context
from app.ingestion.service import BoardSyncService
from app.models.ingestion import ATSBoard
from app.models.job_listing import JobListing


async def seed_database_catalog(yaml_path: Path) -> None:
    """
    Parse declarative seed catalog and upsert employers into ats_board.
    Preserves existing sync timestamps and statistics.
    """
    if not yaml_path.exists():
        print(f"❌ Seed catalog file not found: {yaml_path}")
        return

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    boards_data = data.get("boards", [])
    if not boards_data:
        print("⚠️ No board definitions found in catalog.")
        return

    print(f"\n🌱 Seeding database from {yaml_path.name} ({len(boards_data)} boards)...")

    inserted_count = 0
    updated_count = 0

    async with get_session_context() as session:
        for entry in boards_data:
            prov = str(entry["provider"]).lower().strip()
            slug = str(entry["slug"]).lower().strip()
            company_name = str(entry["company_name"]).strip()
            industry = str(entry["industry"]).strip()
            country = entry.get("headquarters_country")
            country_code = entry.get("headquarters_country_code")
            region = entry.get("primary_region")
            tier = int(entry.get("tier", 1))
            priority = int(entry.get("priority", 5))

            stmt = select(ATSBoard).where(
                ATSBoard.provider == prov,
                ATSBoard.slug == slug,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if existing is None:
                new_board = ATSBoard(
                    provider=prov,
                    slug=slug,
                    company_name=company_name,
                    industry=industry,
                    headquarters_country=country,
                    headquarters_country_code=country_code,
                    primary_region=region,
                    tier=tier,
                    priority=priority,
                    is_active=True,
                    discovered_via="seed",
                    next_sync_at=datetime.now(UTC),
                )
                session.add(new_board)
                inserted_count += 1
            else:
                existing.company_name = company_name
                existing.industry = industry
                existing.headquarters_country = country
                existing.headquarters_country_code = country_code
                existing.primary_region = region
                existing.tier = tier
                existing.priority = priority
                existing.is_active = True
                updated_count += 1

        await session.flush()

    print(
        f"✅ Seeding complete: {inserted_count} new boards added, {updated_count} updated.\n"
    )


async def print_statistics() -> None:
    """Print multi-dimensional repository metrics across sectors, geos, and modalities."""
    async with get_session_context() as session:
        # Total jobs
        total_stmt = (
            select(func.count())
            .select_from(JobListing)
            .where(JobListing.status == "active")
        )
        total_jobs = (await session.execute(total_stmt)).scalar() or 0

        # Total registered boards
        total_boards_stmt = (
            select(func.count())
            .select_from(ATSBoard)
            .where(ATSBoard.is_active.is_(True))
        )
        total_boards = (await session.execute(total_boards_stmt)).scalar() or 0

        # By Industry Sector
        sector_stmt = (
            select(JobListing.industry, func.count(JobListing.id))
            .where(JobListing.status == "active")
            .group_by(JobListing.industry)
            .order_by(func.count(JobListing.id).desc())
        )
        sector_counts = (await session.execute(sector_stmt)).all()

        # By Country Code
        country_stmt = (
            select(JobListing.country_code, func.count(JobListing.id))
            .where(JobListing.status == "active")
            .group_by(JobListing.country_code)
            .order_by(func.count(JobListing.id).desc())
            .limit(10)
        )
        country_counts = (await session.execute(country_stmt)).all()

        # By Workplace Modality
        modality_stmt = (
            select(JobListing.workplace_type, func.count(JobListing.id))
            .where(JobListing.status == "active")
            .group_by(JobListing.workplace_type)
            .order_by(func.count(JobListing.id).desc())
        )
        modality_counts = (await session.execute(modality_stmt)).all()

        # By Visa Sponsorship
        visa_stmt = (
            select(JobListing.visa_sponsorship, func.count(JobListing.id))
            .where(JobListing.status == "active")
            .group_by(JobListing.visa_sponsorship)
            .order_by(func.count(JobListing.id).desc())
        )
        visa_counts = (await session.execute(visa_stmt)).all()

        # Top 10 employers
        company_stmt = (
            select(JobListing.company_name, func.count(JobListing.id))
            .where(JobListing.status == "active")
            .group_by(JobListing.company_name)
            .order_by(func.count(JobListing.id).desc())
            .limit(10)
        )
        company_counts = (await session.execute(company_stmt)).all()

        print("\n" + "=" * 65)
        print("📊 CAREER-OS REPOSITORY & INGESTION TELEMETRY")
        print("=" * 65)
        print(f"Total Active Job Postings : {total_jobs}")
        print(f"Registered Career Boards  : {total_boards}")
        print("-" * 65)

        print("\n📂 Breakdown by Industry Sector:")
        if not sector_counts:
            print("  (No listings yet)")
        for sec, cnt in sector_counts:
            sec_label = sec or "unclassified"
            print(f"  • {sec_label:25} : {cnt:4} postings")

        print("\n🌍 Breakdown by Country:")
        if not country_counts:
            print("  (No listings yet)")
        for ctry, cnt in country_counts:
            ctry_label = ctry or "Unspecified/Remote"
            print(f"  • {ctry_label:25} : {cnt:4} postings")

        print("\n🏢 Workplace Modality:")
        for mod, cnt in modality_counts:
            mod_label = mod or "unspecified"
            print(f"  • {mod_label:25} : {cnt:4} postings")

        print("\n🛂 Visa Sponsorship Policy:")
        for v, cnt in visa_counts:
            v_label = v if v is not None else "unspecified/null"
            print(f"  • {v_label:25} : {cnt:4} postings")

        print("\n🏆 Top Employers by Open Roles:")
        if not company_counts:
            print("  (No listings yet)")
        for comp, cnt in company_counts:
            print(f"  • {comp:25} : {cnt:4} postings")
        print("=" * 65 + "\n")


async def crawl_board(
    provider: str, slug: str, company_name: str | None = None
) -> None:
    """Crawl a single employer career board and upsert jobs to PostgreSQL."""
    label = company_name or slug.capitalize()
    print(f"\n🚀 Crawling {label} ({provider.upper()}: {slug})...")
    async with get_session_context() as session:
        service = BoardSyncService(session)
        try:
            run = await service.sync_board(provider, slug)
            print(f"   Status  : {run.status}")
            print(f"   Fetched : {run.fetched_count} open jobs")
            print(f"   New     : {run.new_count} inserted")
            print(f"   Updated : {run.updated_count} updated")
            print(f"   Closed  : {run.closed_count} closed")
            print(f"   Latency : {run.duration_ms}ms")
        except Exception as exc:  # noqa: BLE001
            print(f"   ❌ Crawl failed for {slug}: {exc}")


async def crawl_selected_boards(
    provider: str | None = None,
    slug: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    region: str | None = None,
    due_only: bool = False,
    limit: int | None = None,
    concurrency: int = 6,
) -> None:
    """Query ATSBoard table with multi-dimensional criteria and execute sync with bounded concurrency."""
    async with get_session_context() as session:
        stmt = select(ATSBoard).where(ATSBoard.is_active.is_(True))

        if provider:
            stmt = stmt.where(ATSBoard.provider == provider.lower().strip())
        if slug:
            stmt = stmt.where(ATSBoard.slug == slug.lower().strip())
        if industry:
            stmt = stmt.where(ATSBoard.industry == industry.lower().strip())
        if country:
            stmt = stmt.where(
                (ATSBoard.headquarters_country_code == country.upper().strip())
                | (ATSBoard.headquarters_country.ilike(f"%{country.strip()}%"))
            )
        if region:
            stmt = stmt.where(ATSBoard.primary_region == region.lower().strip())
        if due_only:
            now = datetime.now(UTC)
            stmt = stmt.where(
                (ATSBoard.next_sync_at.is_(None)) | (ATSBoard.next_sync_at <= now)
            )

        stmt = stmt.order_by(
            ATSBoard.priority.desc(), ATSBoard.last_synced_at.asc().nulls_first()
        )
        if limit:
            stmt = stmt.limit(limit)

        boards = (await session.execute(stmt)).scalars().all()

    if not boards:
        print("⚠️ No matching boards found in database for the given criteria.")
        return

    bounded_concurrency = max(1, min(concurrency, 10))
    print(
        f"\n🌐 Executing sync for {len(boards)} matching career boards (concurrency={bounded_concurrency})..."
    )
    sem = asyncio.Semaphore(bounded_concurrency)

    async def _crawl_with_sem(b: ATSBoard) -> None:
        async with sem:
            await crawl_board(b.provider, b.slug, b.company_name)

    await asyncio.gather(*[_crawl_with_sem(b) for b in boards])

    await print_statistics()


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Career-OS Job Crawler & Ingestion CLI (1,000+ Boards Scale)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display multi-dimensional job and board statistics",
    )
    parser.add_argument(
        "--seed-db",
        action="store_true",
        help="Seed ats_board table with the declarative catalog from data/seed_boards.yaml",
    )
    parser.add_argument(
        "--catalog-path",
        default="data/seed_boards.yaml",
        help="Path to YAML board seed catalog (default: data/seed_boards.yaml)",
    )
    parser.add_argument(
        "--provider",
        choices=["greenhouse", "lever", "ashby", "workable", "smartrecruiters"],
        help="Filter by ATS Provider (greenhouse, lever, ashby, workable, smartrecruiters)",
    )
    parser.add_argument(
        "--slug",
        help="Filter by specific company board slug (e.g. janestreet, hrt, stripe, openai)",
    )
    parser.add_argument(
        "--industry",
        help=(
            "Filter by industry sector code "
            "(e.g. hft_quant_trading, fintech, healthtech, ai_machine_learning, devops_infra, cybersecurity)"
        ),
    )
    parser.add_argument(
        "--country",
        help="Filter by country or country code (e.g. US, CA, GB, NL, AU, NZ)",
    )
    parser.add_argument(
        "--region",
        help="Filter by primary region (e.g. north_america, europe, united_kingdom, oceania, canada)",
    )
    parser.add_argument(
        "--due",
        action="store_true",
        help="Crawl only boards whose next_sync_at timestamp is due",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Crawl all registered active boards in the database",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of boards to crawl in this execution batch",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=6,
        help="Concurrent boards to crawl in parallel (default: 6, max: 10)",
    )

    args = parser.parse_args()

    if args.seed_db:
        catalog_file = _PROJECT_ROOT / args.catalog_path
        await seed_database_catalog(catalog_file)
        if not (args.industry or args.provider or args.slug or args.all):
            await print_statistics()
            return

    if args.stats:
        await print_statistics()
        return

    # Direct single-board crawl
    if (
        args.provider
        and args.slug
        and not (args.industry or args.country or args.region or args.all)
    ):
        await crawl_board(args.provider, args.slug)
        await print_statistics()
        return

    # Filtered multi-board crawl
    if (
        args.industry
        or args.country
        or args.region
        or args.due
        or args.all
        or args.provider
        or args.slug
    ):
        await crawl_selected_boards(
            provider=args.provider,
            slug=args.slug,
            industry=args.industry,
            country=args.country,
            region=args.region,
            due_only=args.due,
            limit=args.limit,
            concurrency=args.concurrency,
        )
        return

    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
