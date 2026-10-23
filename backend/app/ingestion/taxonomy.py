"""
Deterministic skills, location, and visa sponsorship taxonomy normalizers.

Maps free-text job attributes into strict relational columns:
- SKILL_TAXONOMY: Technical skill alias mapping
- LocationNormalizer: Extracts city, state, country, modality, and scope
- VisaSponsorshipParser: Multi-jurisdiction immigration classifier (US, CA, UK, AU, EU)
"""

import re
from dataclasses import dataclass, field
from typing import Final

# Canonical skill name -> list of aliases/patterns (case-insensitive)
SKILL_TAXONOMY: Final[dict[str, list[str]]] = {
    # Languages
    "Python": ["python", "python3", "py"],
    "TypeScript": ["typescript", "ts"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "Java": ["java", "jvm"],
    "C++": ["c++", "cpp"],
    "SQL": ["sql"],
    # Backend Frameworks
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Express": ["express", "express.js"],
    "Spring Boot": ["spring boot", "springboot", "spring"],
    # AI / LLM / Multi-Agent
    "LangGraph": ["langgraph"],
    "LangChain": ["langchain"],
    "LlamaIndex": ["llamaindex"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", "tf"],
    "Hugging Face": ["hugging face", "huggingface"],
    "pgvector": ["pgvector", "pg-vector"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    # Data & Databases
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "Redis": ["redis"],
    "MongoDB": ["mongodb", "mongo"],
    "Elasticsearch": ["elasticsearch", "elastic"],
    "Cassandra": ["cassandra"],
    "Snowflake": ["snowflake"],
    "Kafka": ["kafka", "apache kafka"],
    # DevOps, Cloud & Infra
    "Docker": ["docker", "containerization", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Azure": ["azure", "microsoft azure"],
    "Terraform": ["terraform", "tf"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "github actions"],
    # Frontend
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],
    "GraphQL": ["graphql"],
    "REST": ["rest", "restful", "rest api"],
    # HealthTech & Clinical Regulatory Protocols
    "EDI 837": ["edi 837", "837p", "837i", "837d", "x12 837", "edi 837 claims"],
    "EDI 835": ["edi 835", "835 era", "x12 835", "electronic remittance advice"],
    "HL7": ["hl7", "hl7v2", "hl7 v2", "hl7 standards"],
    "FHIR": ["fhir", "hl7 fhir", "smart on fhir", "fhir api"],
    "DICOM": ["dicom", "dicom protocol", "medical imaging protocol"],
    "HIPAA": ["hipaa", "hipaa compliance", "phi protection", "hitech act"],
    "ICD-10": ["icd-10", "icd10", "cpt codes", "hcpcs"],
    "Prior Authorization": [
        "prior authorization",
        "prior auth",
        "claims adjudication",
        "utilization management",
    ],
    "EHR": [
        "ehr",
        "emr",
        "electronic health records",
        "epic systems",
        "cerner",
    ],
    # FinTech & Capital Markets Protocols
    "PCI-DSS": ["pci-dss", "pci compliance", "pci dss"],
    "FIX Protocol": ["fix protocol", "financial information exchange", "fix engine"],
    "ISO 20022": ["iso 20022", "swift messaging", "ach processing"],
    "KYC/AML": ["kyc", "aml", "anti-money laundering", "know your customer"],
    # Security, Compliance & GovTech Protocols
    "FedRAMP": ["fedramp", "fedramp high", "fedramp moderate", "il4", "il5"],
    "SOC 2": ["soc 2", "soc2", "soc 2 type ii", "soc2 type 2"],
}


# US State Postal Codes -> State Names
US_STATES: Final[dict[str, str]] = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

# Canadian Province Codes -> Names
CA_PROVINCES: Final[dict[str, str]] = {
    "ON": "Ontario",
    "BC": "British Columbia",
    "QC": "Quebec",
    "AB": "Alberta",
    "MB": "Manitoba",
    "SK": "Saskatchewan",
    "NS": "Nova Scotia",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "PE": "Prince Edward Island",
}

# Australian State Codes -> Names
AU_STATES: Final[dict[str, str]] = {
    "NSW": "New South Wales",
    "VIC": "Victoria",
    "QLD": "Queensland",
    "WA": "Western Australia",
    "SA": "South Australia",
    "TAS": "Tasmania",
    "ACT": "Australian Capital Territory",
}


@dataclass
class NormalizedLocation:
    """Structured location output."""

    raw_location: str
    city: str | None = None
    state_province: str | None = None
    state_province_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    primary_region: str | None = None
    workplace_type: str = "on_site"  # on_site, hybrid, remote
    # none, state_province, country_wide, regional_timezone, worldwide_global
    remote_scope: str = "none"


class LocationNormalizer:
    """Normalizes unstructured location strings into granular geographical fields."""

    @classmethod
    def normalize(cls, raw: str | None) -> NormalizedLocation:
        if not raw or not raw.strip():
            return NormalizedLocation(
                raw_location="Remote",
                workplace_type="remote",
                remote_scope="worldwide_global",
            )

        text = raw.strip()
        lower = text.lower()

        # 1. Workplace Modality
        workplace_type = "on_site"
        if "hybrid" in lower:
            workplace_type = "hybrid"
        elif "remote" in lower:
            workplace_type = "remote"

        # 2. Remote Scope
        remote_scope = "none"
        if workplace_type == "remote":
            if any(
                term in lower
                for term in ["worldwide", "global", "anywhere", "all locations"]
            ):
                remote_scope = "worldwide_global"
            elif any(
                term in lower
                for term in ["emea", "apac", "latam", "americas", "europe"]
            ):
                remote_scope = "regional_timezone"
            elif any(
                term in lower
                for term in [
                    "us only",
                    "usa only",
                    "canada only",
                    "uk only",
                    "australia only",
                ]
            ):
                remote_scope = "country_wide"
            else:
                remote_scope = "country_wide"

        city: str | None = None
        state_province: str | None = None
        state_province_code: str | None = None
        country: str | None = None
        country_code: str | None = None
        primary_region: str | None = None

        # Clean parts split by comma or pipe or slash
        parts = [p.strip() for p in re.split(r"[,|\/–-]+", text) if p.strip()]

        # Check for UK
        uk_cities = {
            "london",
            "edinburgh",
            "manchester",
            "cambridge",
            "bristol",
            "birmingham",
            "oxford",
            "belfast",
            "glasgow",
        }
        if (
            any(c in lower for c in uk_cities)
            or "united kingdom" in lower
            or " uk" in lower
            or lower.endswith("uk")
            or "england" in lower
            or "scotland" in lower
        ):
            country = "United Kingdom"
            country_code = "GB"
            primary_region = "europe"
            for p in parts:
                if p.lower() in uk_cities:
                    city = p.title()
                    break

        # Check for Australia
        elif "australia" in lower or any(
            re.search(rf"\b{code}\b", text) for code in AU_STATES
        ):
            country = "Australia"
            country_code = "AU"
            primary_region = "oceania"
            for code, name in AU_STATES.items():
                if re.search(rf"\b{code}\b", text) or name.lower() in lower:
                    state_province_code = code
                    state_province = name
                    break
            au_cities = ["sydney", "melbourne", "brisbane", "perth", "adelaide"]
            for p in parts:
                if p.lower() in au_cities:
                    city = p.title()
                    break

        # Check for Canada
        elif (
            "canada" in lower
            or any(re.search(rf"\b{code}\b", text) for code in CA_PROVINCES)
            or any(name.lower() in lower for name in CA_PROVINCES.values())
        ):
            country = "Canada"
            country_code = "CA"
            primary_region = "canada"
            for code, name in CA_PROVINCES.items():
                if re.search(rf"\b{code}\b", text) or name.lower() in lower:
                    state_province_code = code
                    state_province = name
                    break
            if (
                parts
                and parts[0].upper() not in CA_PROVINCES
                and parts[0].lower() not in ["canada", "remote"]
            ):
                city = parts[0].title()
            au_cities = ["sydney", "melbourne", "brisbane", "perth", "adelaide"]
            for p in parts:
                if p.lower() in au_cities:
                    city = p.title()
                    break

        # Check for New Zealand
        elif "new zealand" in lower or " nz" in lower or lower.endswith("nz"):
            country = "New Zealand"
            country_code = "NZ"
            primary_region = "anz"
            nz_cities = ["auckland", "wellington", "christchurch"]
            for p in parts:
                if p.lower() in nz_cities:
                    city = p.title()
                    break

        # Check for Europe Tech Hubs
        elif any(
            term in lower
            for term in [
                "germany",
                "berlin",
                "munich",
                "netherlands",
                "amsterdam",
                "france",
                "paris",
                "ireland",
                "dublin",
                "switzerland",
                "zurich",
                "sweden",
                "stockholm",
                "spain",
                "madrid",
                "barcelona",
            ]
        ):
            primary_region = "europe"
            if "germany" in lower or "berlin" in lower or "munich" in lower:
                country = "Germany"
                country_code = "DE"
                city = (
                    "Berlin"
                    if "berlin" in lower
                    else ("Munich" if "munich" in lower else None)
                )
            elif "netherlands" in lower or "amsterdam" in lower:
                country = "Netherlands"
                country_code = "NL"
                city = "Amsterdam"
            elif "france" in lower or "paris" in lower:
                country = "France"
                country_code = "FR"
                city = "Paris"
            elif "ireland" in lower or "dublin" in lower:
                country = "Ireland"
                country_code = "IE"
                city = "Dublin"
            elif "switzerland" in lower or "zurich" in lower:
                country = "Switzerland"
                country_code = "CH"
                city = "Zurich"
            elif "sweden" in lower or "stockholm" in lower:
                country = "Sweden"
                country_code = "SE"
                city = "Stockholm"

        # Check for United States (Default for US states & major US cities)
        else:
            us_city_detected = False
            for code, name in US_STATES.items():
                if re.search(rf"\b{code}\b", text) or name.lower() in lower:
                    state_province_code = code
                    state_province = name
                    country = "United States"
                    country_code = "US"
                    primary_region = "north_america"
                    us_city_detected = True
                    break
            if us_city_detected and parts:
                candidate_city = parts[0]
                if (
                    candidate_city.upper() not in US_STATES
                    and candidate_city.lower()
                    not in ["united states", "usa", "us", "remote"]
                ):
                    city = candidate_city.title()
            elif "united states" in lower or "usa" in lower or "us remote" in lower:
                country = "United States"
                country_code = "US"
                primary_region = "north_america"

        return NormalizedLocation(
            raw_location=text,
            city=city,
            state_province=state_province,
            state_province_code=state_province_code,
            country=country,
            country_code=country_code,
            primary_region=primary_region,
            workplace_type=workplace_type,
            remote_scope=remote_scope,
        )


@dataclass
class ParsedVisaPolicy:
    """Structured visa policy output."""

    status: str | None  # 'yes', 'no', 'transfer_only', 'opt_cpt_accepted', None
    notes: str | None
    visa_types: list[str] = field(default_factory=list)


class VisaSponsorshipParser:
    """Parses immigration and work authorization terms from job descriptions."""

    GATE_REGEX: Final[re.Pattern[str]] = re.compile(
        r"\b(visa|sponsorship|sponsor|h-?1b|opt|cpt|lmia|"
        r"skilled worker|subclass 482|blue card)\b",
        re.IGNORECASE,
    )

    NEGATIVE_PATTERNS: Final[list[re.Pattern[str]]] = [
        re.compile(r"without (?:requiring |need for )?sponsorship", re.IGNORECASE),
        re.compile(
            r"(?:do not|cannot|unable to|will not) (?:provide |offer )?sponsor",
            re.IGNORECASE,
        ),
        re.compile(
            r"no (?:visa )?sponsorship (?:available|provided|offered)", re.IGNORECASE
        ),
        re.compile(
            r"not (?:currently )?eligible for (?:visa )?sponsorship", re.IGNORECASE
        ),
        re.compile(
            r"must be (?:legally )?authorized to work in "
            r"(?:the us|canada|the uk) without",
            re.IGNORECASE,
        ),
    ]

    TRANSFER_ONLY_REGEX: Final[re.Pattern[str]] = re.compile(
        r"(?:only (?:accepting|supporting) )?(?:h-?1b|visa) transfers? only",
        re.IGNORECASE,
    )

    OPT_CPT_REGEX: Final[re.Pattern[str]] = re.compile(
        r"\b(?:f-?1 )?(?:opt|cpt|stem opt)\b", re.IGNORECASE
    )

    @classmethod
    def parse(cls, raw_description: str | None) -> ParsedVisaPolicy:
        if not raw_description or not raw_description.strip():
            return ParsedVisaPolicy(status=None, notes=None, visa_types=[])

        text = raw_description.strip()

        # Gate Check: If no immigration terms exist, zero overhead return None
        if not cls.GATE_REGEX.search(text):
            return ParsedVisaPolicy(status=None, notes=None, visa_types=[])

        # Extract relevant sentence window
        sentences = re.split(r"(?<=[.!?])\s+", text)
        relevant_sentences = [s.strip() for s in sentences if cls.GATE_REGEX.search(s)]
        best_sentence = relevant_sentences[0] if relevant_sentences else text[:200]

        # Check Negatives
        for neg_pat in cls.NEGATIVE_PATTERNS:
            if neg_pat.search(best_sentence) or neg_pat.search(text):
                return ParsedVisaPolicy(status="no", notes=best_sentence, visa_types=[])

        # Check Transfer Only
        if cls.TRANSFER_ONLY_REGEX.search(text):
            return ParsedVisaPolicy(
                status="transfer_only", notes=best_sentence, visa_types=["us_h1b"]
            )

        # Check OPT / CPT Affirmative
        if cls.OPT_CPT_REGEX.search(text) and not any(
            neg.search(text) for neg in cls.NEGATIVE_PATTERNS
        ):
            return ParsedVisaPolicy(
                status="opt_cpt_accepted",
                notes=best_sentence,
                visa_types=["us_opt_cpt"],
            )

        # Check Affirmative Sponsorship across jurisdictions
        visa_types: list[str] = []
        lower = text.lower()
        if "h-1b" in lower or "h1b" in lower:
            visa_types.append("us_h1b")
        if "lmia" in lower or "global skills" in lower:
            visa_types.append("ca_lmia")
        if "skilled worker" in lower:
            visa_types.append("uk_skilled_worker")
        if "subclass 482" in lower or "tss" in lower:
            visa_types.append("au_subclass_482")
        if "blue card" in lower:
            visa_types.append("eu_blue_card")

        if any(
            term in lower
            for term in [
                "sponsor visa",
                "visa sponsorship",
                "provide sponsorship",
                "offer sponsorship",
                "open to visa",
            ]
        ):
            return ParsedVisaPolicy(
                status="yes", notes=best_sentence, visa_types=visa_types
            )

        return ParsedVisaPolicy(status=None, notes=best_sentence, visa_types=visa_types)
