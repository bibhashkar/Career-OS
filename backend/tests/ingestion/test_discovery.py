"""
Unit tests for BoardDiscoveryEngine (slug generation, probing, and snowballing).
"""

from pathlib import Path

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.discovery import BoardDiscoveryEngine, generate_candidate_slugs
from app.models.ingestion import ATSBoard

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_generate_candidate_slugs() -> None:
    # Test simple company name
    slugs = generate_candidate_slugs("Stripe")
    assert "stripe" in slugs
    assert "stripehq" in slugs

    # Test company with Inc/spaces and domain
    slugs_domain = generate_candidate_slugs("Linear Orbit, Inc.", domain="linear.app")
    assert "linear" in slugs_domain
    assert "linear-orbit-inc" in slugs_domain or "linearorbitinc" in slugs_domain


@pytest.mark.asyncio
async def test_snowball_from_apply_url(db_session: AsyncSession) -> None:
    engine = BoardDiscoveryEngine(db_session)

    # Ingest a job link found on an aggregator
    apply_url = "https://boards.greenhouse.io/figma/jobs/555123"
    board = await engine.snowball_from_apply_url(
        apply_url=apply_url,
        company_name="Figma",
        domain="figma.com",
    )

    assert board is not None
    assert board.provider == "greenhouse"
    assert board.slug == "figma"
    assert board.discovered_via == "snowball"
    assert board.tier == 1

    # Verify record in database
    stmt = select(ATSBoard).where(ATSBoard.slug == "figma")
    stored = (await db_session.execute(stmt)).scalar_one()
    assert stored.company_name == "Figma"


@pytest.mark.asyncio
async def test_probe_company_boards_discovers_valid_slug(
    db_session: AsyncSession,
) -> None:
    # Mock transport responding 200 for 'stripe' on greenhouse and 404 for other slugs
    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "boards-api.greenhouse.io/v1/boards/stripe/jobs" in url_str:
            return httpx.Response(200, json={"jobs": [{"id": 1}]})
        return httpx.Response(404, json={"error": "not found"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    engine = BoardDiscoveryEngine(db_session, client=client)

    discovered = await engine.probe_company_boards("Stripe", domain="stripe.com")
    assert len(discovered) == 1
    board = discovered[0]
    assert board.provider == "greenhouse"
    assert board.slug == "stripe"
    assert board.discovered_via == "probe"
