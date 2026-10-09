"""
Unit tests for ProvenanceCompanyIntelProvider, GitHubOrgVerifier, and Google News RSS.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.company_intel_provider import ProvenanceCompanyIntelProvider
from app.ingestion.github_verifier import GitHubOrgVerifier
from app.ingestion.models import DataOrigin
from app.ingestion.news import fetch_company_news_rss
from app.models.company_dossier import CompanyDossier


@pytest.mark.asyncio
async def test_github_org_verifier_validates_matching_domain() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        url_str = str(request.url)
        if "/orgs/stripe/repos" in url_str:
            return httpx.Response(
                200,
                json=[
                    {"name": "stripe-python", "language": "Python"},
                    {"name": "sorbet", "language": "Ruby"},
                ],
            )
        elif "/orgs/stripe" in url_str:
            return httpx.Response(200, json={"blog": "https://stripe.com"})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    verifier = GitHubOrgVerifier(client=client)

    result = await verifier.fetch_verified_org_tech_stack("stripe", "stripe.com")
    assert result is not None
    assert "Python" in result["languages"]
    assert "Ruby" in result["languages"]
    assert "stripe-python" in result["repos"]


@pytest.mark.asyncio
async def test_github_org_verifier_rejects_mismatched_domain() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # Organization homepage does not match the company target domain
        return httpx.Response(200, json={"blog": "https://othercompany.com"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    verifier = GitHubOrgVerifier(client=client)

    # linear.app vs othercompany.com
    result = await verifier.fetch_verified_org_tech_stack("linear", "linear.app")
    assert result is None  # Safely rejected due to entity collision guard


@pytest.mark.asyncio
async def test_fetch_company_news_rss_parses_feed() -> None:
    sample_xml = """<rss version="2.0">
      <channel>
        <title>Google News</title>
        <item>
          <title>Stripe Launches New Agentic Payment API - TechCrunch</title>
          <link>https://news.example.com/stripe-agent-api</link>
          <pubDate>Mon, 05 Oct 2026 14:00:00 GMT</pubDate>
          <source>TechCrunch</source>
        </item>
      </channel>
    </rss>"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=sample_xml)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    news = await fetch_company_news_rss("Stripe", client=client)

    assert len(news) == 1
    item = news[0]
    assert "Stripe Launches New Agentic Payment API" in item["title"]
    assert item["date"] == "2026-10-05"
    assert item["source"] == "TechCrunch"


@pytest.mark.asyncio
async def test_provenance_company_intel_provider_end_to_end(
    db_session: AsyncSession,
) -> None:
    verifier = GitHubOrgVerifier()
    verifier.fetch_verified_org_tech_stack = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "org": "acme",
            "languages": ["Go", "TypeScript"],
            "repos": ["acme-core"],
            "verified_domain": "https://acme.com",
        }
    )

    with patch(
        "app.ingestion.company_intel_provider.fetch_company_news_rss",
        new=AsyncMock(
            return_value=[
                {
                    "title": "Acme releases v2.0",
                    "date": "2026-10-01",
                    "source": "PR Newswire",
                    "url": "https://example.com/acme-v2",
                }
            ]
        ),
    ):
        provider = ProvenanceCompanyIntelProvider(
            session=db_session, github_verifier=verifier
        )

        job_desc = "Building distributed payment gateways with Python and PostgreSQL."
        dossier = await provider.fetch_company_intel(
            company_name="Acme Corp",
            domain="acme.com",
            job_description=job_desc,
        )

        assert dossier.company_name == "Acme Corp"
        assert "Python" in dossier.tech_stack
        assert "PostgreSQL" in dossier.tech_stack
        assert "Go" in dossier.tech_stack
        assert "TypeScript" in dossier.tech_stack
        assert len(dossier.recent_news) == 1
        assert dossier.data_origin == DataOrigin.LIVE

        # Check provenance audit trail
        assert "tech_stack" in dossier.field_provenance
        assert dossier.field_provenance["tech_stack"].method == "verified"
        assert (
            "source:job_description"
            in dossier.field_provenance["tech_stack"].source_urls
        )

        # Verify persisted row in database
        stmt = select(CompanyDossier).where(CompanyDossier.company_name == "Acme Corp")
        record = (await db_session.execute(stmt)).scalar_one()
        assert record.canonical_name == "Acme Corp"
        assert record.last_fetched_at is not None
        assert "tech_stack" in record.field_provenance
