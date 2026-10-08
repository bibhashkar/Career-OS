"""
Pre-seeded tier-1 ATS career boards for prominent technology companies.

Enables immediate unmetered ingestion for high-profile companies without
reliance on paid aggregator APIs.
"""

from typing import Any

from app.ingestion.models import ATSProvider

# Curated seed boards with verified ATS providers and public slugs
INITIAL_SEED_BOARDS: list[dict[str, Any]] = [
    {
        "provider": ATSProvider.GREENHOUSE,
        "slug": "stripe",
        "company_name": "Stripe",
        "domain": "stripe.com",
        "tier": 1,
        "priority": 10,
    },
    {
        "provider": ATSProvider.GREENHOUSE,
        "slug": "openai",
        "company_name": "OpenAI",
        "domain": "openai.com",
        "tier": 1,
        "priority": 10,
    },
    {
        "provider": ATSProvider.GREENHOUSE,
        "slug": "anthropic",
        "company_name": "Anthropic",
        "domain": "anthropic.com",
        "tier": 1,
        "priority": 10,
    },
    {
        "provider": ATSProvider.GREENHOUSE,
        "slug": "figma",
        "company_name": "Figma",
        "domain": "figma.com",
        "tier": 1,
        "priority": 9,
    },
    {
        "provider": ATSProvider.GREENHOUSE,
        "slug": "cloudflare",
        "company_name": "Cloudflare",
        "domain": "cloudflare.com",
        "tier": 1,
        "priority": 9,
    },
    {
        "provider": ATSProvider.GREENHOUSE,
        "slug": "airbnb",
        "company_name": "Airbnb",
        "domain": "airbnb.com",
        "tier": 1,
        "priority": 8,
    },
    {
        "provider": ATSProvider.LEVER,
        "slug": "postman",
        "company_name": "Postman",
        "domain": "postman.com",
        "tier": 1,
        "priority": 8,
    },
    {
        "provider": ATSProvider.ASHBY,
        "slug": "linear",
        "company_name": "Linear",
        "domain": "linear.app",
        "tier": 1,
        "priority": 9,
    },
    {
        "provider": ATSProvider.ASHBY,
        "slug": "ramp",
        "company_name": "Ramp",
        "domain": "ramp.com",
        "tier": 1,
        "priority": 9,
    },
    {
        "provider": ATSProvider.ASHBY,
        "slug": "replit",
        "company_name": "Replit",
        "domain": "replit.com",
        "tier": 1,
        "priority": 8,
    },
]
