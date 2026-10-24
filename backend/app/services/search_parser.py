"""
Tokenizer and entity extraction service for the Command-Facet Omnibar.

Parses free-text search input into structured entity filters (companies,
industries, seniorities, modalities, and technical skills) and separates
residual text for downstream BM25 or vector retrieval.
Target budget: < 2ms per query.
"""

import re
from typing import Any

from app.schemas.search import TokenizedFilterExtractionDTO
from app.services.skill_graph import (
    CANONICAL_SKILL_ALIASES,
    SPECIFICITY_TIERS,
)

# ---------------------------------------------------------------------------
# Canonical In-Memory Dictionaries
# ---------------------------------------------------------------------------
CANONICAL_COMPANIES: set[str] = {
    # Tech Giants & Platforms
    "stripe",
    "google",
    "meta",
    "apple",
    "amazon",
    "microsoft",
    "netflix",
    # HealthTech
    "epic systems",
    "epic",
    "optum",
    "cerner",
    "veeva",
    "flatiron health",
    "athenahealth",
    "oscar health",
    "teladoc",
    # FinTech & Capital Markets
    "plaid",
    "brex",
    "ramp",
    "robinhood",
    "chime",
    "affirm",
    "block",
    "citadel",
    "two sigma",
    "jane street",
    "hudson river trading",
    "optiver",
    "jump trading",
    "drw",
    "virtu",
    # AI/ML & Compute
    "openai",
    "anthropic",
    "cohere",
    "databricks",
    "scale ai",
    "hugging face",
    "mistral ai",
    "weights & biases",
    # Cloud & DevTools
    "hashicorp",
    "docker",
    "datadog",
    "gitlab",
    "github",
    "vercel",
    "postman",
    "supabase",
    # Gaming & AdTech
    "riot games",
    "blizzard",
    "electronic arts",
    "epic games",
    "unity",
    "roblox",
    "ubisoft",
    "respawn",
    "the trade desk",
    "applovin",
    "criteo",
    "magnite",
    "integral ad science",
    # Enterprise SaaS & E-Commerce
    "atlassian",
    "salesforce",
    "dropbox",
    "zendesk",
    "asana",
    "slack",
    "notion",
    "hubspot",
    "shopify",
    "wayfair",
    "instacart",
    "doordash",
}

CANONICAL_INDUSTRIES: dict[str, str] = {
    "healthtech": "healthtech",
    "healthcare": "healthtech",
    "healthcare_it": "healthtech",
    "healthcare it": "healthtech",
    "health tech": "healthtech",
    "health": "healthtech",
    "clinical": "healthtech",
    "fintech": "fintech",
    "financial tech": "fintech",
    "banking": "fintech",
    "payments": "fintech",
    "hft": "hft_quant_trading",
    "quant": "hft_quant_trading",
    "quant trading": "hft_quant_trading",
    "trading": "hft_quant_trading",
    "ai": "ai_ml_infra",
    "ai/ml": "ai_ml_infra",
    "ai_ml": "ai_ml_infra",
    "ml": "ai_ml_infra",
    "machine learning": "ai_ml_infra",
    "devtools": "devtools",
    "developer tools": "devtools",
    "infrastructure": "devtools",
    "cloud": "devtools",
    "cybersecurity": "cybersecurity",
    "security": "cybersecurity",
    "infosec": "cybersecurity",
    "gaming": "gaming",
    "games": "gaming",
    "game dev": "gaming",
    "adtech": "adtech",
    "ad tech": "adtech",
    "advertising": "adtech",
    "saas": "general_saas",
    "enterprise saas": "general_saas",
    "general saas": "general_saas",
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "commerce": "ecommerce",
    "retail": "ecommerce",
}

CANONICAL_SENIORITIES: dict[str, str] = {
    "intern": "intern",
    "internship": "intern",
    "entry": "entry",
    "entry-level": "entry",
    "entry level": "entry",
    "junior": "junior",
    "jr": "junior",
    "mid": "mid",
    "mid-level": "mid",
    "mid level": "mid",
    "senior": "senior",
    "sr": "senior",
    "lead": "lead",
    "staff": "staff",
    "principal": "principal",
    "director": "director",
}

CANONICAL_MODALITIES: dict[str, str] = {
    "remote": "remote",
    "wfh": "remote",
    "hybrid": "hybrid",
    "flexible": "hybrid",
    "on-site": "on_site",
    "onsite": "on_site",
    "in-office": "on_site",
    "office": "on_site",
}


class OmnisearchParser:
    """
    Sub-2ms natural language query tokenizer and entity extractor.
    Maps free-form text tokens into structured facet criteria.
    """

    @staticmethod
    def parse_query(raw_text: str) -> TokenizedFilterExtractionDTO:
        """
        Extracts recognized entities into structured buckets and returns
        a TokenizedFilterExtractionDTO with residual query string.

        Args:
            raw_text: Free-text search string entered in the omnibar.

        Returns:
            TokenizedFilterExtractionDTO containing extracted entities
            and residual_query string.
        """
        extracted: dict[str, Any] = {
            "companies": [],
            "target_industries": [],
            "seniority_levels": [],
            "workplace_modality": None,
            "must_have_skills": [],
        }

        working_text = raw_text.strip()
        if not working_text:
            return TokenizedFilterExtractionDTO()

        # Normalize multiple spaces and split
        tokens = re.split(r"\s+", working_text)
        residual_tokens: list[str] = []

        i = 0
        n = len(tokens)

        while i < n:
            word = tokens[i].lower()
            two_word = f"{tokens[i]} {tokens[i + 1]}".lower() if i + 1 < n else ""
            three_word = (
                f"{tokens[i]} {tokens[i + 1]} {tokens[i + 2]}".lower()
                if i + 2 < n
                else ""
            )

            # 1. Tri-word company or industry matching
            if three_word in CANONICAL_COMPANIES:
                extracted["companies"].append(three_word)
                i += 3
                continue
            if three_word in CANONICAL_INDUSTRIES:
                vert = CANONICAL_INDUSTRIES[three_word]
                if vert not in extracted["target_industries"]:
                    extracted["target_industries"].append(vert)
                i += 3
                continue

            # 2. Two-word company matching (e.g. "epic systems", "riot games")
            if two_word in CANONICAL_COMPANIES:
                extracted["companies"].append(two_word)
                i += 2
                continue

            # 3. Two-word industry matching (e.g. "health tech", "quant trading")
            if two_word in CANONICAL_INDUSTRIES:
                vert = CANONICAL_INDUSTRIES[two_word]
                if vert not in extracted["target_industries"]:
                    extracted["target_industries"].append(vert)
                i += 2
                continue

            # 4. Two-word seniority (e.g. "entry level", "mid level")
            if two_word in CANONICAL_SENIORITIES:
                sen = CANONICAL_SENIORITIES[two_word]
                if sen not in extracted["seniority_levels"]:
                    extracted["seniority_levels"].append(sen)
                i += 2
                continue

            # 5. Two-word modality (e.g. "on site", "in office")
            if two_word in CANONICAL_MODALITIES and not extracted["workplace_modality"]:
                extracted["workplace_modality"] = CANONICAL_MODALITIES[two_word]
                i += 2
                continue

            # 5b. Two-word technical skills (e.g. "machine learning", "unit testing")
            clean_two = two_word.strip(" ,.;:")
            if clean_two in CANONICAL_SKILL_ALIASES or clean_two in SPECIFICITY_TIERS:
                canonical_s = CANONICAL_SKILL_ALIASES.get(clean_two, clean_two)
                if canonical_s not in extracted["must_have_skills"]:
                    extracted["must_have_skills"].append(canonical_s)
                i += 2
                continue

            # 6. Single-word company matching (e.g. "stripe", "optum")
            if word in CANONICAL_COMPANIES:
                extracted["companies"].append(word)
                i += 1
                continue

            # 7. Single-word industry vertical
            if word in CANONICAL_INDUSTRIES:
                vert = CANONICAL_INDUSTRIES[word]
                if vert not in extracted["target_industries"]:
                    extracted["target_industries"].append(vert)
                i += 1
                continue

            # 8. Single-word seniority
            if word in CANONICAL_SENIORITIES:
                sen = CANONICAL_SENIORITIES[word]
                if sen not in extracted["seniority_levels"]:
                    extracted["seniority_levels"].append(sen)
                i += 1
                continue

            # 9. Single-word modality
            if word in CANONICAL_MODALITIES and not extracted["workplace_modality"]:
                extracted["workplace_modality"] = CANONICAL_MODALITIES[word]
                i += 1
                continue

            # 10. Technical skills matching (e.g. "kubernetes", "fastapi", "fhir")
            clean_word = word.strip(" ,.;:")
            if clean_word in CANONICAL_SKILL_ALIASES or clean_word in SPECIFICITY_TIERS:
                canonical_s = CANONICAL_SKILL_ALIASES.get(clean_word, clean_word)
                if canonical_s not in extracted["must_have_skills"]:
                    extracted["must_have_skills"].append(canonical_s)
                i += 1
                continue

            # Residual un-tokenized content
            residual_tokens.append(tokens[i])
            i += 1

        return TokenizedFilterExtractionDTO(
            companies=extracted["companies"],
            target_industries=extracted["target_industries"],
            seniority_levels=extracted["seniority_levels"],
            workplace_modality=extracted["workplace_modality"],
            must_have_skills=extracted["must_have_skills"],
            residual_query=" ".join(residual_tokens).strip(),
        )
