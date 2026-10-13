#!/usr/bin/env python3
"""
Career-OS Ingestion & Crawler CLI.

Directly crawls and synchronizes real job postings from Tier-1 ATS boards
(Greenhouse, Lever, Ashby) without requiring third-party API keys.

Usage:
  # 1. Show current job repository statistics:
  ./.venv/bin/python scripts/crawl_jobs.py --stats

  # 2. Crawl an individual company board:
  ./.venv/bin/python scripts/crawl_jobs.py --provider greenhouse --slug cloudflare
  ./.venv/bin/python scripts/crawl_jobs.py --provider greenhouse --slug stripe
  ./.venv/bin/python scripts/crawl_jobs.py --provider lever --slug netflix
  ./.venv/bin/python scripts/crawl_jobs.py --provider ashby --slug openai

  # 3. Crawl a curated preset of major tech employers:
  ./.venv/bin/python scripts/crawl_jobs.py --preset popular
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports resolve
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
sys.path.insert(0, str(_BACKEND_DIR))

from app.core.database import get_session_context
from app.ingestion.service import BoardSyncService
from app.models.job_listing import JobListing
from sqlalchemy import func, select

# Curated Tier-1 public ATS boards that require 0 API keys
PRESET_BOARDS: list[tuple[str, str, str]] = [
    ("Cloudflare", "greenhouse", "cloudflare"),
    ("Stripe", "greenhouse", "stripe"),
    ("GitLab", "greenhouse", "gitlab"),
    ("Airbnb", "greenhouse", "airbnb"),
    ("Figma", "greenhouse", "figma"),
    ("Netflix", "lever", "netflix"),
    ("Spotify", "lever", "spotify"),
    ("Palantir", "lever", "palantir"),
    ("OpenAI", "ashby", "openai"),
    ("Anthropic", "ashby", "anthropic"),
    ("Retool", "ashby", "retool"),
    ("Ramp", "ashby", "ramp"),
]


async def print_statistics() -> None:
    """Print current repository job count and top companies."""
    async with get_session_context() as session:
        total_stmt = select(func.count()).select_from(JobListing)
        total_jobs = (await session.execute(total_stmt)).scalar() or 0

        company_stmt = (
            select(JobListing.company_name, func.count(JobListing.id))
            .group_by(JobListing.company_name)
            .order_by(func.count(JobListing.id).desc())
            .limit(10)
        )
        company_counts = (await session.execute(company_stmt)).all()

        print("\n" + "=" * 50)
        print("📊 Career-OS Job Repository Statistics")
        print("=" * 50)
        print(f"Total Active Job Listings: {total_jobs}")
        print("\nTop Companies in Database:")
        if not company_counts:
            print("  (No jobs in database yet)")
        for comp, count in company_counts:
            print(f"  • {comp:20} : {count} open roles")
        print("=" * 50 + "\n")


async def crawl_board(
    provider: str, slug: str, company_name: str | None = None
) -> None:
    """Crawl a single board and save jobs to PostgreSQL."""
    label = company_name or slug.capitalize()
    print(f"\n🚀 Crawling {label} ({provider.upper()}: {slug})...")
    async with get_session_context() as session:
        service = BoardSyncService(session)
        try:
            run = await service.sync_board(provider, slug)
            print(f"   Status  : {run.status}")
            print(f"   Fetched : {run.fetched_count} open jobs")
            print(f"   New     : {run.new_count} inserted")
            print(f"   Latency : {run.duration_ms}ms")
        except Exception as exc:  # noqa: BLE001
            print(f"   ❌ Crawl failed for {slug}: {exc}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Career-OS Job Crawler CLI")
    parser.add_argument(
        "--stats", action="store_true", help="Display current job count"
    )
    parser.add_argument(
        "--provider", choices=["greenhouse", "lever", "ashby"], help="ATS Provider"
    )
    parser.add_argument(
        "--slug", help="Company board slug (e.g. stripe, cloudflare, netflix)"
    )
    parser.add_argument(
        "--preset",
        choices=["popular"],
        help="Crawl a curated list of popular employers",
    )

    args = parser.parse_args()

    if args.stats:
        await print_statistics()
        return

    if args.provider and args.slug:
        await crawl_board(args.provider, args.slug)
        await print_statistics()
        return

    if args.preset == "popular":
        print(f"🌐 Crawling {len(PRESET_BOARDS)} curated ATS boards...")
        for comp_name, provider, slug in PRESET_BOARDS:
            await crawl_board(provider, slug, comp_name)
        await print_statistics()
        return

    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
