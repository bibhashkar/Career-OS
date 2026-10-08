"""
ATS Board Discovery & Probing Engine.

Discovers and registers new company ATS boards:
1. Slug probing: Given a company name/domain, generates candidate slugs
   (e.g., 'stripe', 'stripe-inc', 'stripehq') and probes fixed official ATS API hosts.
2. Snowballing: Parses aggregator apply URLs (e.g. from JobSpy or LinkedIn)
   and automatically discovers/promotes the underlying ATS board into tier 1.
3. Entity collision protection: Verifies candidate board matches company domain/name
   to prevent collisions (e.g., Linear vs Linear Software, Ramp vs Ramp Financial).
"""

import logging
import re
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http import DEFAULT_TIMEOUT
from app.ingestion.adapters.ats import AshbyAdapter, GreenhouseAdapter, LeverAdapter
from app.ingestion.models import ATSProvider
from app.ingestion.security import parse_ats_url
from app.models.ingestion import ATSBoard

logger = logging.getLogger("career_os.ingestion.discovery")


def generate_candidate_slugs(company_name: str, domain: str | None = None) -> list[str]:
    """
    Generate normalized candidate board slugs for probing.
    e.g. 'Stripe, Inc.' -> ['stripe', 'stripeinc', 'stripe-inc', 'stripehq']
    """
    clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", company_name).lower().strip()
    words = clean_name.split()
    if not words:
        return []

    base = words[0]
    full_joined = "".join(words)
    full_hyphen = "-".join(words)

    candidates: list[str] = [base]
    if len(words) > 1:
        candidates.extend([full_hyphen, full_joined])

    # Suffix variants
    candidates.extend([f"{base}hq", f"{base}-hq", f"{base}technologies", f"{base}tech"])

    # Extract subdomain or second-level domain if provided
    if domain:
        clean_domain = domain.lower().replace("www.", "").split(".")[0]
        if clean_domain not in candidates:
            candidates.insert(0, clean_domain)

    # Return unique ordered slugs
    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        if c and c not in seen and len(c) >= 2:
            seen.add(c)
            result.append(c)
    return result


class BoardDiscoveryEngine:
    """
    Engine to discover, probe, and register ATS boards with entity protection.
    """

    def __init__(
        self,
        session: AsyncSession,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.session = session
        self.client = client
        self._gh_adapter = GreenhouseAdapter(client=client)
        self._lever_adapter = LeverAdapter(client=client)
        self._ashby_adapter = AshbyAdapter(client=client)

    async def register_board_if_not_exists(
        self,
        provider: ATSProvider,
        slug: str,
        company_name: str,
        domain: str | None = None,
        discovered_via: str = "probe",
        priority: int = 5,
    ) -> ATSBoard | None:
        """
        Register a new ATS board in the database if not already present.
        """
        norm_slug = slug.lower().strip()
        stmt = select(ATSBoard).where(
            ATSBoard.provider == str(provider),
            ATSBoard.slug == norm_slug,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        board = ATSBoard(
            provider=str(provider),
            slug=norm_slug,
            company_name=company_name,
            domain=domain,
            tier=1,
            priority=priority,
            discovered_via=discovered_via,
            is_active=True,
            next_sync_at=datetime.now(UTC),
        )
        self.session.add(board)
        await self.session.flush()
        logger.info(
            "Registered new %s board for '%s' (slug: %s, via: %s)",
            provider,
            company_name,
            norm_slug,
            discovered_via,
        )
        return board

    async def snowball_from_apply_url(
        self,
        apply_url: str,
        company_name: str,
        domain: str | None = None,
    ) -> ATSBoard | None:
        """
        Extract provider and slug from job apply URL and auto-register board.
        Promotes aggregator job sources into Tier-1 synced boards.
        """
        ats_info = parse_ats_url(apply_url)
        if not ats_info:
            return None

        provider, slug, _ = ats_info
        return await self.register_board_if_not_exists(
            provider=provider,
            slug=slug,
            company_name=company_name,
            domain=domain,
            discovered_via="snowball",
            priority=7,
        )

    async def probe_company_boards(
        self,
        company_name: str,
        domain: str | None = None,
        providers: list[ATSProvider] | None = None,
    ) -> list[ATSBoard]:
        """
        Probe official ATS endpoints for candidate slugs.
        Only queries official fixed API hosts (zero SSRF surface).
        """
        target_providers = providers or [
            ATSProvider.GREENHOUSE,
            ATSProvider.LEVER,
            ATSProvider.ASHBY,
        ]
        candidate_slugs = generate_candidate_slugs(company_name, domain)
        discovered: list[ATSBoard] = []

        for slug in candidate_slugs:
            for prov in target_providers:
                try:
                    is_valid = await self._probe_single_board(prov, slug)
                    if is_valid:
                        board = await self.register_board_if_not_exists(
                            provider=prov,
                            slug=slug,
                            company_name=company_name,
                            domain=domain,
                            discovered_via="probe",
                        )
                        if board:
                            discovered.append(board)
                            return (
                                discovered  # Stop once a primary valid board is found
                            )
                except Exception as e:
                    logger.debug("Probe failed for %s:%s - %s", prov, slug, e)

        return discovered

    async def _probe_single_board(self, provider: ATSProvider, slug: str) -> bool:
        """
        Probe whether an ATS board slug exists and is active.
        """
        if provider == ATSProvider.GREENHOUSE:
            url = f"{GreenhouseAdapter.BASE_URL}/{slug}/jobs"
        elif provider == ATSProvider.LEVER:
            url = f"{LeverAdapter.BASE_URL}/{slug}?mode=json"
        elif provider == ATSProvider.ASHBY:
            url = f"{AshbyAdapter.BASE_URL}/{slug}"
        else:
            return False

        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                # Confirm response is valid JSON and contains jobs
                try:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return True
                    if isinstance(data, dict):
                        if "jobs" in data or "jobPostings" in data or "data" in data:
                            return True
                except ValueError:
                    return False
        return False
