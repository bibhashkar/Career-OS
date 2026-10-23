"""
Deterministic requirements extraction and visa status classification.

Pass 1 of the extraction pipeline:
- High-precision matching against curated skills taxonomy.
- Years of experience extraction via robust regex patterns.
- Tri-state visa sponsorship policy classification (yes / no / unknown).
"""

import re

from app.ingestion.models import ParsedRequirementsDTO, VisaSponsorshipStatus
from app.ingestion.taxonomy import SKILL_TAXONOMY

# Regex for years of experience
# (e.g., "5+ years", "3-5 years of experience", "at least 4 years")
YOE_PATTERNS = [
    re.compile(
        r"(\d+)\s*\+?\s*years?(?:\s+(?:of|in))?(?:\s+[\w\-]+)*\s+experience", re.I
    ),
    re.compile(r"(\d+)\s*\+?\s*years?", re.I),
    re.compile(r"at\s+least\s+(\d+)\s*years?", re.I),
    re.compile(r"minimum\s+(?:of\s+)?(\d+)\s*years?", re.I),
    re.compile(r"(\d+)\s*-\s*\d+\s*years?", re.I),
]

# Patterns for negative visa sponsorship ("no")
VISA_NEGATIVE_PATTERNS = [
    re.compile(r"(?:will\s+not|cannot|unable\s+to|not\s+able\s+to)\s+sponsor", re.I),
    re.compile(r"no\s+(?:visa\s+)?sponsorship\s+(?:is\s+)?available", re.I),
    re.compile(r"without\s+(?:the\s+need\s+for\s+)?sponsorship", re.I),
    re.compile(
        r"must\s+be\s+authorized\s+to\s+work\s+without\s+(?:company\s+)?sponsorship",
        re.I,
    ),
    re.compile(r"not\s+offering\s+sponsorship", re.I),
]

# Patterns for positive visa sponsorship ("yes")
VISA_POSITIVE_PATTERNS = [
    re.compile(r"visa\s+sponsorship\s+(?:is\s+)?available", re.I),
    re.compile(r"(?:can|will|able\s+to)\s+sponsor(?:\s+(?:work\s+)?visas?)?", re.I),
    re.compile(r"sponsorship\s+is\s+provided", re.I),
    re.compile(r"willing\s+to\s+sponsor", re.I),
    re.compile(r"relocation\s+and\s+visa\s+sponsorship", re.I),
]

# ---------------------------------------------------------------------------
# Industry Vertical Company and Keyword Patterns
# ---------------------------------------------------------------------------
INDUSTRY_COMPANY_PATTERNS: dict[str, list[str]] = {
    "healthtech": [
        "optum",
        "epic systems",
        "cerner",
        "veeva",
        "oscar health",
        "flatiron health",
        "athenahealth",
        "change healthcare",
        "teladoc",
        "doximity",
        "modern health",
        "ro health",
        "omada health",
        "cityblock",
    ],
    "fintech": [
        "stripe",
        "plaid",
        "square",
        "block",
        "robinhood",
        "coinbase",
        "brex",
        "ramp",
        "chime",
        "affirm",
        "adyen",
        "klarna",
        "revolut",
    ],
    "hft_quant_trading": [
        "citadel",
        "jane street",
        "two sigma",
        "jump trading",
        "hudson river trading",
        "optiver",
        "drw",
        "virtu",
        "imc trading",
        "point72",
    ],
    "cybersecurity": [
        "crowdstrike",
        "palo alto networks",
        "cloudflare",
        "zscaler",
        "sentinelone",
        "okta",
        "snyk",
        "wiz",
        "tanium",
    ],
    "gaming": [
        "riot games",
        "blizzard",
        "electronic arts",
        "epic games",
        "unity technologies",
        "roblox",
        "ubisoft",
        "activision",
        "respawn",
        "bungie",
    ],
    "ecommerce": [
        "shopify",
        "amazon",
        "ebay",
        "etsy",
        "wayfair",
        "instacart",
        "doordash",
        "chewy",
    ],
    "adtech": [
        "the trade desk",
        "applovin",
        "doubleclick",
        "criteo",
        "magnite",
        "integral ad science",
    ],
    "devtools": [
        "github",
        "gitlab",
        "datadog",
        "hashicorp",
        "docker",
        "postman",
        "vercel",
        "supabase",
    ],
    "ai_ml_infra": [
        "openai",
        "anthropic",
        "scale ai",
        "hugging face",
        "cohere",
        "weights & biases",
        "mistral ai",
    ],
}

INDUSTRY_KEYWORD_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "healthtech": [
        re.compile(r"\bhipaa\b", re.I),
        re.compile(r"\behr\b", re.I),
        re.compile(r"\bemr\b", re.I),
        re.compile(r"\bhl7\b", re.I),
        re.compile(r"\bfhir\b", re.I),
        re.compile(r"\bedi\s*837\b", re.I),
        re.compile(r"\bedi\s*835\b", re.I),
        re.compile(r"\bdicom\b", re.I),
        re.compile(r"\bicd-10\b", re.I),
        re.compile(r"\bprior\s+authoriz(?:ation|ed)\b", re.I),
        re.compile(r"\bclaims\s+adjudication\b", re.I),
        re.compile(r"\bhealthtech\b", re.I),
        re.compile(r"\bhealthcare\b", re.I),
        re.compile(r"\bclinical\b", re.I),
        re.compile(r"\bmedical\s+records?\b", re.I),
        re.compile(r"\bpatient\s+care\b", re.I),
        re.compile(r"\bpayer\b", re.I),
        re.compile(r"\btelehealth\b", re.I),
        re.compile(r"\bphi\s+protection\b", re.I),
    ],
    "hft_quant_trading": [
        re.compile(r"\bhft\b", re.I),
        re.compile(r"\bhigh\s+frequency\s+trading\b", re.I),
        re.compile(r"\bquant(?:itative)?\s+trading\b", re.I),
        re.compile(r"\border\s+book\b", re.I),
        re.compile(r"\bfix\s+protocol\b", re.I),
        re.compile(r"\bmarket\s+making\b", re.I),
        re.compile(r"\blow\s+latency\s+c\+\+\b", re.I),
    ],
    "fintech": [
        re.compile(r"\bfintech\b", re.I),
        re.compile(r"\bpci-dss\b", re.I),
        re.compile(r"\biso\s*20022\b", re.I),
        re.compile(r"\bkyc\b", re.I),
        re.compile(r"\baml\b", re.I),
        re.compile(r"\banti-money\s+laundering\b", re.I),
        re.compile(r"\bach\s+processing\b", re.I),
        re.compile(r"\bswift\s+messaging\b", re.I),
        re.compile(r"\bpayment\s+gateway\b", re.I),
        re.compile(r"\bcredit\s+card\s+processing\b", re.I),
        re.compile(r"\bgeneral\s+ledger\b", re.I),
        re.compile(r"\bbanking\b", re.I),
    ],
    "cybersecurity": [
        re.compile(r"\bcybersecurity\b", re.I),
        re.compile(r"\binfosec\b", re.I),
        re.compile(r"\bsiem\b", re.I),
        re.compile(r"\bfedramp\b", re.I),
        re.compile(r"\bsoc\s*2\b", re.I),
        re.compile(r"\bthreat\s+intelligence\b", re.I),
        re.compile(r"\bzero\s+trust\b", re.I),
        re.compile(r"\bpenetration\s+testing\b", re.I),
        re.compile(r"\bvulnerability\s+management\b", re.I),
    ],
    "gaming": [
        re.compile(r"\bgame\s+engine\b", re.I),
        re.compile(r"\bgameplay\b", re.I),
        re.compile(r"\bunreal\s+engine\b", re.I),
        re.compile(r"\bunity3d\b", re.I),
        re.compile(r"\bmatchmaking\s+servers?\b", re.I),
        re.compile(r"\bleaderboards?\b", re.I),
        re.compile(r"\bmultiplayer\s+game\b", re.I),
        re.compile(r"\bgaming\b", re.I),
    ],
    "adtech": [
        re.compile(r"\badtech\b", re.I),
        re.compile(r"\bad\s+tech\b", re.I),
        re.compile(r"\brtb\b", re.I),
        re.compile(r"\breal-time\s+bidding\b", re.I),
        re.compile(r"\bdemand-side\s+platform\b", re.I),
        re.compile(r"\bsupply-side\s+platform\b", re.I),
        re.compile(r"\bad\s+serving\b", re.I),
        re.compile(r"\bimpression\s+telemetry\b", re.I),
    ],
    "ecommerce": [
        re.compile(r"\be-?commerce\b", re.I),
        re.compile(r"\bshopping\s+cart\b", re.I),
        re.compile(r"\bcheckout\s+flow\b", re.I),
        re.compile(r"\binventory\s+management\b", re.I),
        re.compile(r"\bretail\s+tech\b", re.I),
    ],
    "devtools": [
        re.compile(r"\bdev\s*tools\b", re.I),
        re.compile(r"\bdeveloper\s+tools\b", re.I),
        re.compile(r"\bdeveloper\s+productivity\b", re.I),
        re.compile(r"\bobservability\b", re.I),
        re.compile(r"\bapm\b", re.I),
    ],
    "ai_ml_infra": [
        re.compile(r"\bmodel\s+serving\b", re.I),
        re.compile(r"\bgpu\s+cluster\b", re.I),
        re.compile(r"\bcuda\s+kernel\b", re.I),
        re.compile(r"\bvllm\b", re.I),
        re.compile(r"\btriton\s+(?:inference\s+)?server\b", re.I),
        re.compile(r"\bllm\s+infrastructure\b", re.I),
    ],
}

DOMAIN_MANDATE_PATTERNS = [
    re.compile(
        r"(?:healthcare|healthtech|clinical|ehr|emr|hipaa|fintech|banking|financial|"
        r"trading|hft|gaming|cybersecurity|security|adtech|ecommerce)\s+"
        r"(?:experience|background|domain|industry|knowledge)\s+"
        r"(?:is\s+)?(?:required|mandatory|essential|strongly\s+preferred|must\s+have|prerequisite)",
        re.I,
    ),
    re.compile(
        r"must\s+have\s+(?:prior\s+)?(?:experience\s+in|background\s+in)\s+"
        r"(?:healthcare|healthtech|clinical|ehr|hipaa|fintech|banking|trading|hft|gaming|cybersecurity)",
        re.I,
    ),
    re.compile(
        r"(?:required|mandatory)\s*:\s*.*(?:healthcare|healthtech|clinical|ehr|hipaa|"
        r"fintech|banking|trading|hft|gaming|cybersecurity)",
        re.I,
    ),
]

DEEP_REGULATORY_PROTOCOLS = [
    re.compile(r"\bedi\s*837\b", re.I),
    re.compile(r"\bedi\s*835\b", re.I),
    re.compile(r"\bhl7\b", re.I),
    re.compile(r"\bfhir\b", re.I),
    re.compile(r"\bdicom\b", re.I),
    re.compile(r"\bicd-10\b", re.I),
    re.compile(r"\bprior\s+authoriz(?:ation|ed)\b", re.I),
    re.compile(r"\bclaims\s+adjudication\b", re.I),
    re.compile(r"\bfix\s+protocol\b", re.I),
    re.compile(r"\bpci-dss\b", re.I),
    re.compile(r"\biso\s*20022\b", re.I),
    re.compile(r"\bfedramp\b", re.I),
]


def classify_industry_vertical(
    title: str,
    raw_description: str,
    company_name: str = "",
) -> str:
    """
    Classify the primary vertical of a job posting based on employer and text markers.
    """
    combined = f"{title}\n{raw_description}"
    scores: dict[str, int] = {k: 0 for k in INDUSTRY_KEYWORD_PATTERNS}

    comp_lower = company_name.strip().lower()
    if comp_lower:
        if comp_lower in ("epic", "epic systems"):
            scores["healthtech"] += 10
        elif "epic games" in comp_lower:
            scores["gaming"] += 10
        else:
            for industry, companies in INDUSTRY_COMPANY_PATTERNS.items():
                for c in companies:
                    if c in comp_lower:
                        scores[industry] += 10
                        break

    for industry, patterns in INDUSTRY_KEYWORD_PATTERNS.items():
        count = sum(1 for p in patterns if p.search(combined))
        scores[industry] += count

    best_industry, best_score = max(scores.items(), key=lambda x: x[1])
    if best_score > 0:
        return best_industry

    return "general_saas"


def extract_domain_strictness(
    title: str,
    raw_description: str,
    industry_vertical: str,
) -> float:
    """
    Extract domain strictness tier (beta_domain in [0.0, 1.0]).

    - 1.0 (Strict/Regulated): Explicit domain mandates, deep regulatory protocols,
      or 3+ domain-specific markers.
    - 0.5 (Preferred): Industry-specific role without strict regulatory mandate.
    - 0.0 (Domain Agnostic): General SaaS or no domain markers found.
    """
    if industry_vertical == "general_saas":
        return 0.0

    combined = f"{title}\n{raw_description}"

    # 1. Explicit domain mandate regex
    for pat in DOMAIN_MANDATE_PATTERNS:
        if pat.search(combined):
            return 1.0

    # 2. Deep regulatory protocols present
    for pat in DEEP_REGULATORY_PROTOCOLS:
        if pat.search(combined):
            return 1.0

    # 3. 3+ domain markers in the identified vertical
    patterns = INDUSTRY_KEYWORD_PATTERNS.get(industry_vertical, [])
    match_count = sum(1 for p in patterns if p.search(combined))
    if match_count >= 3:
        return 1.0

    # Default for identified vertical: preferred
    return 0.5


def classify_visa_sponsorship(text: str) -> VisaSponsorshipStatus:
    """
    Classify visa sponsorship as YES, NO, or UNKNOWN based on text evidence.
    Negative patterns take priority to protect candidate from ineligible roles.
    """
    if not text:
        return VisaSponsorshipStatus.UNKNOWN

    for pat in VISA_NEGATIVE_PATTERNS:
        if pat.search(text):
            return VisaSponsorshipStatus.NO

    for pat in VISA_POSITIVE_PATTERNS:
        if pat.search(text):
            return VisaSponsorshipStatus.YES

    return VisaSponsorshipStatus.UNKNOWN


def extract_years_of_experience(text: str) -> int | None:
    """
    Extract minimum required years of experience from description text.
    """
    if not text:
        return None

    yoe_found: list[int] = []
    for pat in YOE_PATTERNS:
        matches = pat.findall(text)
        for m in matches:
            try:
                yoe_found.append(int(m))
            except ValueError:
                pass

    if yoe_found:
        # Return reasonable minimum (between 1 and 20)
        valid = [y for y in yoe_found if 1 <= y <= 20]
        if valid:
            return min(valid)
    return None


def extract_deterministic_requirements(
    title: str,
    raw_description: str,
    company_name: str = "",
) -> ParsedRequirementsDTO:
    """
    Deterministic Pass 1:
    Extracts skills, minimum experience, visa status, industry vertical,
    and domain strictness without any LLM cost.
    """
    combined_text = f"{title}\n{raw_description}"
    words_boundary_text = f" {combined_text.lower()} "

    detected_skills: list[str] = []
    evidence: dict[str, list[str]] = {}

    for canonical_name, aliases in SKILL_TAXONOMY.items():
        matched_aliases: list[str] = []
        for alias in aliases:
            # Word boundary check to prevent substring false-positives
            pattern = rf"(?:\b|_){re.escape(alias.lower())}(?:\b|_)"
            if re.search(pattern, words_boundary_text):
                matched_aliases.append(alias)

        if matched_aliases:
            detected_skills.append(canonical_name)
            evidence[canonical_name] = matched_aliases

    # Sort alphabetically for consistency
    detected_skills.sort()

    yoe = extract_years_of_experience(combined_text)
    visa_status = classify_visa_sponsorship(combined_text)
    industry_vertical = classify_industry_vertical(title, raw_description, company_name)
    domain_strictness = extract_domain_strictness(
        title, raw_description, industry_vertical
    )

    return ParsedRequirementsDTO(
        required_skills=detected_skills,
        preferred_skills=[],
        min_experience_years=yoe,
        visa_sponsorship=visa_status,
        extraction_version="v1-deterministic",
        confidence_score=0.95 if detected_skills else 0.5,
        needs_review=False,
        industry_vertical=industry_vertical,
        domain_strictness=domain_strictness,
        evidence=evidence,
    )
