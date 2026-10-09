"""
Provenance-tracked company intelligence provider.

Replaces paid Exa / Apollo services with verified, unmetered multi-source synthesis:
1. Sourced from the Job Description itself (primary truth).
2. Company's verified GitHub organization languages & public repositories.
3. Google News RSS for recent dated developments (7-day TTL).
4. Stored field-level provenance audit trail:
   {method: verified|inferred|unknown, source_urls: [...], confidence, fetched_at}.
5. Stale-while-revalidate with refresh scheduling.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.deterministic_extractor import extract_deterministic_requirements
from app.ingestion.github_verifier import GitHubOrgVerifier
from app.ingestion.models import (
    CompanyDossierDTO,
    DataOrigin,
    FieldProvenanceDTO,
)
from app.ingestion.news import fetch_company_news_rss
from app.ingestion.ports.provider import CompanyIntelProviderPort
from app.models.company_dossier import CompanyDossier

logger = logging.getLogger("career_os.ingestion.intel")


class ProvenanceCompanyIntelProvider(CompanyIntelProviderPort):
    """
    Synthesizes company dossiers with strict source grounding and provenance.
    """

    def __init__(
        self,
        session: AsyncSession,
        github_verifier: GitHubOrgVerifier | None = None,
    ) -> None:
        self.session = session
        self.github_verifier = github_verifier or GitHubOrgVerifier()

    async def fetch_company_intel(
        self,
        company_name: str,
        domain: str | None = None,
        job_description: str | None = None,
    ) -> CompanyDossierDTO:
        """
        Retrieve or refresh company intelligence with field-level provenance.
        """
        canonical_name = company_name.strip()
        norm_name = canonical_name.lower()
        now = datetime.now(UTC)

        # 1. Check existing cached dossier in database
        stmt = select(CompanyDossier).where(
            CompanyDossier.company_name.ilike(canonical_name)
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        if existing and existing.last_fetched_at:
            # Check if cache is still fresh (7 days for news, 90 days for tech stack)
            is_stale = existing.next_refresh_at and now >= existing.next_refresh_at
            if not is_stale:
                provenance_map: dict[str, FieldProvenanceDTO] = {}
                for k, v in (existing.field_provenance or {}).items():
                    if isinstance(v, dict):
                        provenance_map[k] = FieldProvenanceDTO(**v)

                return CompanyDossierDTO(
                    company_name=existing.company_name,
                    canonical_name=existing.canonical_name or existing.company_name,
                    domain=existing.domain,
                    industry=existing.industry,
                    tech_stack=list(existing.tech_stack or []),
                    recent_news=list(existing.recent_news or []),
                    business_model=existing.business_model,
                    culture_notes=existing.culture_notes,
                    data_origin=DataOrigin(existing.data_origin),
                    field_provenance=provenance_map,
                    last_fetched_at=existing.last_fetched_at,
                    next_refresh_at=existing.next_refresh_at,
                )

        # 2. Extract tech stack evidence from Job Description if provided
        tech_stack: set[str] = set()
        provenance: dict[str, FieldProvenanceDTO] = {}

        if job_description:
            parsed = extract_deterministic_requirements(canonical_name, job_description)
            for skill in parsed.required_skills:
                tech_stack.add(skill)
            if tech_stack:
                provenance["tech_stack"] = FieldProvenanceDTO(
                    method="verified",
                    source_urls=["source:job_description"],
                    confidence=1.0,
                    fetched_at=now,
                )

        # 3. Query verified GitHub Organization
        github_data = None
        candidate_org = norm_name.replace(" ", "").replace("-", "")
        try:
            github_data = await self.github_verifier.fetch_verified_org_tech_stack(
                candidate_org=candidate_org,
                company_domain=domain,
            )
            if github_data:
                for lang in github_data.get("languages", []):
                    tech_stack.add(lang)
                if "tech_stack" not in provenance:
                    provenance["tech_stack"] = FieldProvenanceDTO(
                        method="verified",
                        source_urls=[f"https://github.com/{candidate_org}"],
                        confidence=0.95,
                        fetched_at=now,
                    )
                else:
                    provenance["tech_stack"].source_urls.append(
                        f"https://github.com/{candidate_org}"
                    )
        except Exception as e:
            logger.debug("GitHub org verification skipped: %s", e)

        # 4. Fetch Google News RSS (7-day TTL)
        news_items: list[dict[str, Any]] = []
        try:
            news_items = await fetch_company_news_rss(canonical_name, max_items=4)
            if news_items:
                provenance["recent_news"] = FieldProvenanceDTO(
                    method="verified",
                    source_urls=[
                        item.get("url", "") for item in news_items if item.get("url")
                    ],
                    confidence=0.9,
                    fetched_at=now,
                )
        except Exception as e:
            logger.debug("News RSS fetch skipped: %s", e)

        # 5. Build DTO
        resolved_domain = domain or (
            github_data.get("verified_domain") if github_data else None
        )
        sorted_stack = sorted(tech_stack)
        next_refresh = now + timedelta(days=7)

        dto = CompanyDossierDTO(
            company_name=canonical_name,
            canonical_name=canonical_name,
            domain=resolved_domain,
            industry=existing.industry if existing else None,
            tech_stack=sorted_stack,
            recent_news=news_items,
            business_model=existing.business_model if existing else None,
            culture_notes=existing.culture_notes if existing else None,
            data_origin=DataOrigin.LIVE,
            field_provenance=provenance,
            last_fetched_at=now,
            next_refresh_at=next_refresh,
        )

        # 6. Upsert dossier record into database
        provenance_dict = {k: v.model_dump(mode="json") for k, v in provenance.items()}

        if existing is None:
            new_record = CompanyDossier(
                company_name=canonical_name,
                canonical_name=canonical_name,
                domain=resolved_domain,
                industry=dto.industry,
                tech_stack=sorted_stack,
                recent_news=news_items,
                business_model=dto.business_model,
                culture_notes=dto.culture_notes,
                data_origin=str(DataOrigin.LIVE),
                field_provenance=provenance_dict,
                last_fetched_at=now,
                next_refresh_at=next_refresh,
            )
            self.session.add(new_record)
        else:
            existing.canonical_name = canonical_name
            existing.domain = resolved_domain or existing.domain
            if sorted_stack:
                existing.tech_stack = sorted_stack
            if news_items:
                existing.recent_news = news_items
            existing.data_origin = str(DataOrigin.LIVE)
            existing.field_provenance = provenance_dict
            existing.last_fetched_at = now
            existing.next_refresh_at = next_refresh

        await self.session.flush()
        return dto
