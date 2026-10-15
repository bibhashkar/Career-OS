"""
Unit test asserting the integrity and schema validity of data/seed_boards.yaml.
Prevents broken slugs, duplicate boards, or invalid taxonomy from violating
foreign keys or constraints in PostgreSQL.
"""

import re
from pathlib import Path

import yaml

from app.ingestion.models import ATSProviderEnum

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATALOG_PATH = _PROJECT_ROOT / "data" / "seed_boards.yaml"

VALID_SECTORS = {
    "hft_quant_trading",
    "fintech",
    "healthtech",
    "biotech",
    "ai_ml_infra",
    "ai_machine_learning",
    "blockchain_web3",
    "devtools",
    "devops_infra",
    "cybersecurity",
    "enterprise_saas",
    "cleantech_climate",
    "ecommerce_retail",
    "gaming_entertainment",
    "aerospace_defense",
    "hardware_iot",
    "proptech",
    "edtech",
    "legaltech",
}

SLUG_PATTERN = re.compile(r"^[a-z0-9_\-]+$")
ISO_COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")


def test_seed_catalog_integrity() -> None:
    assert CATALOG_PATH.exists(), f"Seed catalog not found at {CATALOG_PATH}"

    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    assert "boards" in data, "Catalog YAML missing top-level 'boards' key"

    boards = data["boards"]
    assert len(boards) >= 150, f"Expected at least 150 seed boards, found {len(boards)}"

    valid_providers = {p.value for p in ATSProviderEnum}
    seen_keys: set[tuple[str, str]] = set()

    for idx, entry in enumerate(boards):
        # 1. Required fields
        for req in ["slug", "company_name", "provider", "industry", "tier", "priority"]:
            assert req in entry, (
                f"Board #{idx} ({entry.get('slug')}) missing required field '{req}'"
            )

        provider = str(entry["provider"]).lower().strip()
        slug = str(entry["slug"]).lower().strip()
        industry = str(entry["industry"]).strip()
        tier = entry["tier"]
        priority = entry["priority"]

        # 2. Provider validation
        assert provider in valid_providers, (
            f"Board #{idx} ({slug}) has invalid provider '{provider}'."
        )

        # 3. Slug format validation
        assert SLUG_PATTERN.match(slug), (
            f"Board #{idx} has invalid slug '{slug}'. Must match pattern."
        )

        # 4. Composite uniqueness: (provider, slug)
        key = (provider, slug)
        assert key not in seen_keys, (
            f"Duplicate board definition detected for {provider}:{slug}"
        )
        seen_keys.add(key)

        # 5. Industry taxonomy check (must match industry_sector foreign key)
        assert industry in VALID_SECTORS, (
            f"Board #{idx} ({slug}) has unapproved industry '{industry}'."
        )

        # 6. Tier and Priority ranges
        assert isinstance(tier, int) and 1 <= tier <= 3, (
            f"Board #{idx} ({slug}) tier must be int 1-3, got {tier}"
        )
        assert isinstance(priority, int) and 1 <= priority <= 10, (
            f"Board #{idx} ({slug}) priority must be int 1-10, got {priority}"
        )

        # 7. ISO Country code format (if provided)
        country_code = entry.get("headquarters_country_code")
        if country_code:
            assert ISO_COUNTRY_PATTERN.match(country_code), (
                f"Board #{idx} ({slug}) code '{country_code}' must be 2-letter ISO"
            )
