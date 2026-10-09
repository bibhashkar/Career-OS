"""
Verified GitHub organization crawler and tech stack analyzer.

Extracts top repositories and languages for an employer's official GitHub org,
verifying that the organization's homepage matches the company domain to prevent
wrong-entity collisions (e.g. Linear vs Linear Software, Ramp vs Ramp Financial).
"""

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.http import DEFAULT_TIMEOUT
from app.ingestion.security import sanitize_text

logger = logging.getLogger("career_os.ingestion.github")

GITHUB_API_BASE = "https://api.github.com"


class GitHubOrgVerifier:
    """
    Finds and verifies official GitHub organizations matching employer domain.
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    def _normalize_domain(self, domain: str | None) -> str:
        """Strip http/https, www, and trailing slashes for comparison."""
        if not domain:
            return ""
        d = domain.lower().strip()
        if d.startswith("http://") or d.startswith("https://"):
            parsed = urlparse(d)
            d = parsed.netloc
        if d.startswith("www."):
            d = d[4:]
        return d.split("/")[0]

    async def fetch_verified_org_tech_stack(
        self,
        candidate_org: str,
        company_domain: str | None,
    ) -> dict[str, Any] | None:
        """
        Verify GitHub org homepage matches company domain and extract top languages.
        Returns dict with {"org": ..., "languages": [...], "repos": [...]} or None.
        """
        if not candidate_org:
            return None

        clean_org = candidate_org.lower().strip()
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Career-OS-Ingestion/1.0",
        }

        async with self.client or httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            # 1. Fetch organization details
            org_resp = await client.get(
                f"{GITHUB_API_BASE}/orgs/{clean_org}", headers=headers
            )
            if org_resp.status_code != 200:
                return None

            org_data = org_resp.json()
            blog_url = org_data.get("blog", "")

            # 2. Entity safety: Verify organization website matches company domain
            if company_domain:
                norm_target = self._normalize_domain(company_domain)
                norm_org_site = self._normalize_domain(blog_url)
                if norm_target and norm_org_site and norm_target != norm_org_site:
                    logger.warning(
                        "GitHub org '%s' homepage '%s' does not match "
                        "company domain '%s'; rejected.",
                        clean_org,
                        norm_org_site,
                        norm_target,
                    )
                    return None

            # 3. Fetch top public repositories
            repos_resp = await client.get(
                f"{GITHUB_API_BASE}/orgs/{clean_org}/repos?type=public&sort=pushed&per_page=15",
                headers=headers,
            )
            if repos_resp.status_code != 200:
                return None

            repos_data = repos_resp.json()

        languages: set[str] = set()
        repo_names: list[str] = []

        for repo in repos_data:
            lang = repo.get("language")
            if lang:
                languages.add(sanitize_text(lang))
            name = repo.get("name")
            if name:
                repo_names.append(sanitize_text(name))

        return {
            "org": clean_org,
            "languages": sorted(languages),
            "repos": repo_names[:10],
            "verified_domain": blog_url,
        }
