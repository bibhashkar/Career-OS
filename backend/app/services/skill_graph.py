"""
Asymmetric Skill Graph, Directional Transfer Matrix, and IDF Specificity Engine.

This module implements the directional technology transfer DAG and specificity weighting
specified in MATCHING_ENGINE_SPEC.md:
  - Asymmetric Transfer Matrix T(u -> v): Captures directional implication (e.g.
    Kubernetes implies Docker mastery; Docker does NOT imply Kubernetes orchestration).
  - Two-hop transitive decay for multi-step technology adjacency.
  - Canonical skill alias normalizer resolving variant surface forms.
  - Inverse Document Frequency (IDF) specificity weighting w(s) to eliminate the
    1/N keyword-stuffing fallacy.
  - Core dealbreaker multiplier D_core penalizing missing critical competencies.
  - Cold-start profile handling for candidates with fewer than 3 atomic CV blocks.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("career_os.services.skill_graph")

# ---------------------------------------------------------------------------
# Canonical Skill Alias Normalization Map
# ---------------------------------------------------------------------------
CANONICAL_SKILL_ALIASES: dict[str, str] = {
    # Orchestration & Containers
    "k8s": "kubernetes",
    "k8": "kubernetes",
    "kube": "kubernetes",
    "container": "containerization",
    "containers": "containerization",
    "docker container": "docker",
    # Languages & Runtimes
    "golang": "go",
    "py": "python",
    "python3": "python",
    "python 3": "python",
    "ts": "typescript",
    "js": "javascript",
    "nodejs": "node.js",
    "node": "node.js",
    "node js": "node.js",
    "cpp": "c++",
    "c plus plus": "c++",
    "c#": "c-sharp",
    "c sharp": "c-sharp",
    # Databases & Storage
    "postgres": "postgresql",
    "postgre": "postgresql",
    "psql": "postgresql",
    "pg": "postgresql",
    "pgvector": "pgvector",
    "mongo": "mongodb",
    "elastic": "elasticsearch",
    "es": "elasticsearch",
    # Frontend Frameworks
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "nextjs": "next.js",
    "next": "next.js",
    "sveltejs": "svelte",
    "svelte.js": "svelte",
    # Cloud Platforms
    "amazon web services": "aws",
    "aws cloud": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "gcp cloud": "gcp",
    "microsoft azure": "azure",
    "azure cloud": "azure",
    # Machine Learning & AI
    "tf": "tensorflow",
    "torch": "pytorch",
    "rag": "retrieval-augmented generation",
    "llm": "large language models",
    "llms": "large language models",
    # Data & Streaming
    "kafka stream": "kafka",
    "kafka streams": "kafka",
    "rabbit": "rabbitmq",
    "rabbit mq": "rabbitmq",
}

# ---------------------------------------------------------------------------
# Asymmetric Transfer Matrix T(u -> v)
# Format: {candidate_skill_u: {job_skill_v: transfer_weight_0_to_1}}
# ---------------------------------------------------------------------------
DIRECT_TRANSFER_MATRIX: dict[str, dict[str, float]] = {
    # -----------------------------------------------------------------------
    # Orchestration & Infrastructure
    # -----------------------------------------------------------------------
    "kubernetes": {
        "docker": 0.90,
        "containerization": 0.95,
        "ecs": 0.80,
        "nomad": 0.75,
        "helm": 0.85,
        "linux": 0.80,
    },
    "helm": {
        "kubernetes": 0.85,
        "docker": 0.80,
    },
    "docker": {
        "containerization": 0.90,
        "podman": 0.85,
        "kubernetes": 0.35,  # Upward / foundation only
        "ecs": 0.50,
    },
    "terraform": {
        "infrastructure as code": 0.95,
        "cloudformation": 0.80,
        "pulumi": 0.80,
        "aws": 0.70,
        "gcp": 0.70,
    },
    # -----------------------------------------------------------------------
    # Cloud Providers (Peer lateral transfer with domain consistency)
    # -----------------------------------------------------------------------
    "aws": {
        "cloud": 0.95,
        "cloud computing": 0.95,
        "gcp": 0.75,
        "azure": 0.75,
    },
    "gcp": {
        "cloud": 0.95,
        "cloud computing": 0.95,
        "aws": 0.75,
        "azure": 0.75,
    },
    "azure": {
        "cloud": 0.95,
        "cloud computing": 0.95,
        "aws": 0.75,
        "gcp": 0.75,
    },
    # -----------------------------------------------------------------------
    # Python Ecosystem
    # -----------------------------------------------------------------------
    "fastapi": {
        "python": 0.95,
        "rest api": 0.90,
        "api design": 0.85,
        "flask": 0.85,
        "django": 0.75,
        "starlette": 0.90,
        "pydantic": 0.95,
        "asyncio": 0.85,
    },
    "django": {
        "python": 0.95,
        "rest api": 0.85,
        "flask": 0.80,
        "fastapi": 0.75,
        "sql": 0.80,
    },
    "flask": {
        "python": 0.95,
        "rest api": 0.85,
        "fastapi": 0.75,
        "django": 0.75,
    },
    "python": {
        "fastapi": 0.35,  # Basic language doesn't grant framework mastery
        "django": 0.30,
        "flask": 0.40,
        "pytorch": 0.25,
        "pandas": 0.40,
    },
    "sqlalchemy": {
        "python": 0.90,
        "sql": 0.90,
        "orm": 0.95,
        "relational database": 0.85,
    },
    "langgraph": {
        "langchain": 0.90,
        "python": 0.90,
        "agentic workflows": 0.95,
        "ai agents": 0.95,
    },
    "langchain": {
        "python": 0.85,
        "langgraph": 0.45,  # Upward: agent graphs require advanced statefulness
        "large language models": 0.80,
    },
    # -----------------------------------------------------------------------
    # Modern JavaScript / TypeScript & Frontend
    # -----------------------------------------------------------------------
    "next.js": {
        "react": 0.95,
        "javascript": 0.95,
        "typescript": 0.85,
        "frontend": 0.90,
        "server-side rendering": 0.95,
        "node.js": 0.80,
    },
    "react": {
        "javascript": 0.90,
        "frontend": 0.90,
        "next.js": 0.65,  # Partial ramp-up to SSR
        "vue": 0.75,
        "angular": 0.65,
        "svelte": 0.70,
    },
    "vue": {
        "javascript": 0.90,
        "frontend": 0.90,
        "react": 0.70,
        "angular": 0.65,
        "svelte": 0.70,
    },
    "angular": {
        "typescript": 0.90,
        "javascript": 0.90,
        "frontend": 0.90,
        "react": 0.65,
        "vue": 0.65,
    },
    "typescript": {
        "javascript": 0.95,
        "typed programming": 0.90,
    },
    "javascript": {
        "typescript": 0.55,  # JS lacks static type system mastery
        "frontend": 0.60,
    },
    # -----------------------------------------------------------------------
    # Systems & Compiled Languages
    # -----------------------------------------------------------------------
    "rust": {
        "systems programming": 0.95,
        "memory safety": 0.95,
        "c++": 0.70,
        "c": 0.75,
        "concurrency": 0.90,
    },
    "tokio": {
        "rust": 0.95,
        "asyncio": 0.85,
        "concurrency": 0.95,
    },
    "c++": {
        "c": 0.90,
        "systems programming": 0.95,
        "rust": 0.60,
        "memory management": 0.95,
    },
    "go": {
        "concurrency": 0.90,
        "microservices": 0.85,
        "backend": 0.85,
    },
    "gin": {
        "go": 0.95,
        "rest api": 0.90,
    },
    "spring boot": {
        "java": 0.95,
        "spring": 0.95,
        "microservices": 0.85,
        "rest api": 0.85,
    },
    "spring": {
        "java": 0.95,
        "spring boot": 0.85,
    },
    "java": {
        "spring boot": 0.40,
        "object-oriented programming": 0.95,
        "kotlin": 0.65,
    },
    # -----------------------------------------------------------------------
    # Distributed Messaging & Streaming
    # -----------------------------------------------------------------------
    "kafka": {
        "event streaming": 0.95,
        "message queues": 0.90,
        "distributed systems": 0.85,
        "rabbitmq": 0.80,  # Kafka translates well to RabbitMQ
        "pulsar": 0.80,
        "kinesis": 0.85,
    },
    "rabbitmq": {
        "message queues": 0.90,
        "amqp": 0.95,
        "kafka": 0.60,  # RabbitMQ does not imply partitioned log streaming
        "activemq": 0.85,
    },
    "pulsar": {
        "kafka": 0.80,
        "event streaming": 0.95,
    },
    # -----------------------------------------------------------------------
    # Relational & NoSQL Databases
    # -----------------------------------------------------------------------
    "postgresql": {
        "sql": 0.95,
        "relational database": 0.95,
        "rdbms": 0.95,
        "mysql": 0.85,
        "sqlite": 0.90,
    },
    "mysql": {
        "sql": 0.95,
        "relational database": 0.95,
        "rdbms": 0.95,
        "postgresql": 0.85,
        "mariadb": 0.95,
    },
    "sql": {
        "postgresql": 0.65,
        "mysql": 0.65,
        "relational database": 0.85,
    },
    "dynamodb": {
        "nosql": 0.95,
        "mongodb": 0.70,
        "key-value store": 0.95,
        "cassandra": 0.60,
    },
    "mongodb": {
        "nosql": 0.95,
        "document database": 0.95,
        "dynamodb": 0.70,
    },
    "cassandra": {
        "nosql": 0.95,
        "distributed systems": 0.85,
        "dynamodb": 0.80,
        "wide-column": 0.95,
    },
    "redis": {
        "caching": 0.95,
        "in-memory database": 0.95,
        "key-value store": 0.95,
        "memcached": 0.90,
    },
    # -----------------------------------------------------------------------
    # AI / Machine Learning Ecosystem
    # -----------------------------------------------------------------------
    "pytorch": {
        "python": 0.95,
        "deep learning": 0.95,
        "machine learning": 0.95,
        "tensorflow": 0.80,
        "keras": 0.85,
        "neural networks": 0.95,
        "jax": 0.70,
    },
    "tensorflow": {
        "python": 0.95,
        "deep learning": 0.95,
        "machine learning": 0.95,
        "pytorch": 0.80,
        "keras": 0.95,
    },
    "jax": {
        "pytorch": 0.85,
        "deep learning": 0.95,
        "python": 0.95,
    },
    "scikit-learn": {
        "machine learning": 0.95,
        "python": 0.95,
        "data science": 0.90,
        "pandas": 0.85,
        "numpy": 0.90,
    },
    "pandas": {
        "python": 0.90,
        "data analysis": 0.90,
        "numpy": 0.85,
        "scikit-learn": 0.50,
    },
}

# ---------------------------------------------------------------------------
# Precomputed Two-Hop Transitive Decay Graph
# Computes T(u -> v) = max_w( T(u -> w) * T(w -> v) * 0.85 )
# ---------------------------------------------------------------------------
TRANSITIVE_TRANSFER_MATRIX: dict[str, dict[str, float]] = {}


def _build_transitive_matrix() -> dict[str, dict[str, float]]:
    """
    Construct bounded 2-hop transitive graph with 0.85 decay factor.

    T_2hop(u -> v) = max_w( T(u -> w) * T(w -> v) * 0.85 )
    Only paths with resulting transfer >= 0.25 are retained.
    """
    matrix: dict[str, dict[str, float]] = {}
    decay = 0.85
    min_threshold = 0.25

    # 1. Seed direct transfers
    for u, targets in DIRECT_TRANSFER_MATRIX.items():
        matrix[u] = dict(targets)

    # 2. Compute 2-hop transfers
    for u, intermediate_map in DIRECT_TRANSFER_MATRIX.items():
        for w, weight_uw in intermediate_map.items():
            if w in DIRECT_TRANSFER_MATRIX:
                for v, weight_wv in DIRECT_TRANSFER_MATRIX[w].items():
                    if v == u:
                        continue
                    two_hop_score = round(weight_uw * weight_wv * decay, 4)
                    if two_hop_score >= min_threshold:
                        existing = matrix[u].get(v, 0.0)
                        if two_hop_score > existing:
                            matrix[u][v] = two_hop_score

    return matrix


TRANSITIVE_TRANSFER_MATRIX = _build_transitive_matrix()

# ---------------------------------------------------------------------------
# Inverse Document Frequency (IDF) / Specificity Weights
# Defines specificity w(s) in [0.4, 2.2] to defeat 1/N keyword stuffing
# ---------------------------------------------------------------------------
SPECIFICITY_TIERS: dict[str, float] = {
    # High-Specificity / Deep Systems (w = 1.8 - 2.2)
    "rust": 2.2,
    "cuda": 2.2,
    "c++": 2.0,
    "langgraph": 2.0,
    "kubernetes": 1.9,
    "kafka": 1.9,
    "distributed systems": 1.9,
    "pgvector": 1.9,
    "cassandra": 1.9,
    "ray": 1.9,
    "spark": 1.9,
    "terraform": 1.8,
    "graphql": 1.8,
    "pytorch": 1.8,
    "jax": 1.8,
    "solidity": 2.0,
    "fpga": 2.2,
    "llvm": 2.2,
    "clickhouse": 1.9,
    "concurrency": 1.8,
    "memory management": 1.9,
    # Standard Production Stack (w = 1.0 - 1.4)
    "python": 1.3,
    "typescript": 1.3,
    "go": 1.4,
    "java": 1.2,
    "react": 1.2,
    "fastapi": 1.4,
    "postgresql": 1.3,
    "aws": 1.3,
    "gcp": 1.3,
    "azure": 1.3,
    "docker": 1.2,
    "redis": 1.2,
    "next.js": 1.3,
    "django": 1.2,
    "flask": 1.1,
    "mysql": 1.1,
    "mongodb": 1.1,
    "dynamodb": 1.2,
    "elasticsearch": 1.3,
    "rabbitmq": 1.2,
    "node.js": 1.2,
    "sql": 1.0,
    "deep learning": 1.4,
    "machine learning": 1.3,
    "containerization": 1.2,
    "rest api": 1.0,
    "api design": 1.1,
    "microservices": 1.2,
    # Commodity / Boilerplate (w = 0.4 - 0.7)
    "git": 0.5,
    "github": 0.5,
    "agile": 0.4,
    "scrum": 0.4,
    "json": 0.4,
    "html": 0.5,
    "css": 0.5,
    "jira": 0.4,
    "linux": 0.7,
    "ci/cd": 0.7,
    "unit testing": 0.6,
    "confluence": 0.4,
    "rest": 0.6,
}

DEFAULT_IDF_WEIGHT = 1.0


@dataclass(frozen=True)
class SkillTransferDetail:
    """Explains how candidate's skill transferred to required job skill."""

    job_skill: str
    candidate_skill: str
    transfer_weight: float
    direction: str  # 'exact', 'implied_prerequisite', 'lateral', 'partial_foundation'


@dataclass(frozen=True)
class SkillGraphEvaluation:
    """Comprehensive multi-factor skill alignment diagnostic."""

    skill_score: float
    d_core: float
    matched_skills: list[str] = field(default_factory=list)
    transferred_skills: list[SkillTransferDetail] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    cold_start_applied: bool = False


# ---------------------------------------------------------------------------
# Normalization & Weight Lookup Utilities
# ---------------------------------------------------------------------------
def normalize_skill(skill: str) -> str:
    """
    Standardize skill token to canonical lowercase alias.

    Strips surrounding whitespace, converts hyphens to spaces where appropriate,
    and applies canonical lookup dictionary.
    """
    if not skill or not skill.strip():
        return ""

    raw = skill.strip().lower()
    # Normalize common punctuation variations
    cleaned = re.sub(r"[\s_]+", " ", raw).strip()

    # Check alias dictionary
    if cleaned in CANONICAL_SKILL_ALIASES:
        return CANONICAL_SKILL_ALIASES[cleaned]

    # Handle dotted extensions (e.g. "vue.js" -> "vue")
    dot_clean = cleaned.replace(".js", "").replace("js", "").strip()
    if dot_clean in CANONICAL_SKILL_ALIASES:
        return CANONICAL_SKILL_ALIASES[dot_clean]

    return cleaned


def get_skill_idf_weight(skill: str, is_core: bool = False) -> float:
    """
    Retrieve Inverse Document Frequency (IDF) specificity weight for a skill.

    Core declared skills receive a 1.25x importance multiplier.
    """
    norm = normalize_skill(skill)
    base_weight = SPECIFICITY_TIERS.get(norm, DEFAULT_IDF_WEIGHT)
    if is_core:
        base_weight *= 1.25
    return round(base_weight, 3)


def get_transfer_weight(candidate_skill: str, job_skill: str) -> float:
    """
    Calculate directional transfer weight T(candidate_skill -> job_skill).

    Returns:
        1.0 for identity (normalized match).
        Weight in [0.25, 0.95] for directed transfers.
        0.0 for unrelated technologies.
    """
    cand_norm = normalize_skill(candidate_skill)
    job_norm = normalize_skill(job_skill)

    if not cand_norm or not job_norm:
        return 0.0

    if cand_norm == job_norm:
        return 1.0

    # Look up precomputed transitive graph (includes direct and 2-hop)
    return TRANSITIVE_TRANSFER_MATRIX.get(cand_norm, {}).get(job_norm, 0.0)


def expand_implied_skills(
    candidate_skills: set[str],
    min_transfer: float = 0.85,
) -> dict[str, float]:
    """
    Expand candidate skills through high-confidence implied transfers.

    Useful for cold-start candidate profiling where candidates declare only
    top-level orchestrators (e.g. 'Kubernetes', 'FastAPI') without explicitly
    re-listing foundational technologies ('Docker', 'Python', 'SQL').

    Args:
        candidate_skills: Raw candidate skill set.
        min_transfer: Minimum transfer threshold (default 0.85).

    Returns:
        Dictionary of {canonical_skill: effective_transfer_weight}.
    """
    expanded: dict[str, float] = {}

    for s in candidate_skills:
        norm = normalize_skill(s)
        if not norm:
            continue
        expanded[norm] = 1.0

        # Discover downstream implied skills
        direct_implied = DIRECT_TRANSFER_MATRIX.get(norm, {})
        for target_skill, weight in direct_implied.items():
            if weight >= min_transfer:
                if weight > expanded.get(target_skill, 0.0):
                    expanded[target_skill] = weight

    return expanded


# ---------------------------------------------------------------------------
# Asymmetric Skill Score & Core Dealbreaker Evaluation Engine
# ---------------------------------------------------------------------------
def compute_asymmetric_skill_score(
    candidate_skills: set[str],
    job_skills: list[str],
    core_job_skills: list[str] | None = None,
    cv_block_count: int = 3,
) -> SkillGraphEvaluation:
    """
    Calculate asymmetric weighted skill overlap S_skills and core dealbreaker D_core.

    Formula:
        S_skills = sum(w(v) * max_{u in C} T(u -> v)) / sum(w(v))
        D_core = product_{v in CoreMissing} 0.70  (floor at 0.25)

    Cold-Start Handling:
        When cv_block_count < 3, automatically activates implied DAG expansion
        and applies a neutral 0.65 prior floor when job requirements are sparse.

    Args:
        candidate_skills: Set of skills declared by or extracted for candidate.
        job_skills: List of required skills specified by job requisition.
        core_job_skills: Optional subset of job skills considered non-negotiable.
        cv_block_count: Number of atomic career blocks in candidate profile.

    Returns:
        SkillGraphEvaluation containing calibrated score and explainability chips.
    """
    clean_job_skills = [normalize_skill(s) for s in job_skills if normalize_skill(s)]
    core_set = {
        normalize_skill(s) for s in (core_job_skills or []) if normalize_skill(s)
    }

    # Job has zero declared skill requirements: return neutral calibrated baseline
    if not clean_job_skills:
        return SkillGraphEvaluation(
            skill_score=0.70,
            d_core=1.0,
            matched_skills=sorted(
                {normalize_skill(s) for s in candidate_skills if normalize_skill(s)}
            )[:5],
            transferred_skills=[],
            missing_skills=[],
            cold_start_applied=False,
        )

    # 1. Cold-Start Expansion if candidate profile is sparse (< 3 CV blocks)
    cold_start_applied = cv_block_count < 3
    if cold_start_applied:
        candidate_map = expand_implied_skills(candidate_skills, min_transfer=0.85)
    else:
        candidate_map = {
            normalize_skill(s): 1.0 for s in candidate_skills if normalize_skill(s)
        }

    matched_skills: list[str] = []
    transferred_details: list[SkillTransferDetail] = []
    missing_skills: list[str] = []
    missing_core_count = 0

    weighted_score_sum = 0.0
    total_weights = 0.0

    for job_s in clean_job_skills:
        is_core = job_s in core_set or SPECIFICITY_TIERS.get(job_s, 1.0) >= 1.8
        w = get_skill_idf_weight(job_s, is_core=is_core)
        total_weights += w

        # Direct identity match
        if job_s in candidate_map:
            match_weight = candidate_map[job_s]
            weighted_score_sum += w * match_weight
            matched_skills.append(job_s)
            continue

        # Asymmetric graph search across candidate skills
        best_u: str | None = None
        best_transfer = 0.0

        for cand_s in candidate_map:
            transfer_w = get_transfer_weight(cand_s, job_s)
            if transfer_w > best_transfer:
                best_transfer = transfer_w
                best_u = cand_s

        if best_transfer >= 0.85 and best_u:
            # High-confidence transfer (e.g. FastAPI -> Python)
            matched_skills.append(job_s)
            transferred_details.append(
                SkillTransferDetail(
                    job_skill=job_s,
                    candidate_skill=best_u,
                    transfer_weight=best_transfer,
                    direction="implied_prerequisite",
                )
            )
            weighted_score_sum += w * best_transfer
        elif best_transfer >= 0.50 and best_u:
            # Lateral or moderate foundation transfer (e.g. AWS -> GCP, Docker -> K8s)
            matched_skills.append(job_s)
            direction = "lateral" if best_transfer >= 0.70 else "partial_foundation"
            transferred_details.append(
                SkillTransferDetail(
                    job_skill=job_s,
                    candidate_skill=best_u,
                    transfer_weight=best_transfer,
                    direction=direction,
                )
            )
            weighted_score_sum += w * best_transfer
        elif best_transfer >= 0.25 and best_u:
            # Weak partial transfer
            weighted_score_sum += w * best_transfer
            missing_skills.append(job_s)
        else:
            # Complete absence of skill
            missing_skills.append(job_s)
            if is_core:
                missing_core_count += 1

    # Raw score calculation
    raw_score = (
        weighted_score_sum / max(total_weights, 0.001) if total_weights > 0 else 0.5
    )

    # Cold-start prior floor: prevent severe false rejections on sparse profiles
    if cold_start_applied and raw_score < 0.65 and len(clean_job_skills) <= 3:
        final_skill_score = max(raw_score, 0.65)
    else:
        final_skill_score = min(1.0, max(0.0, raw_score))

    # Core Dealbreaker Multiplier D_core:
    # Penalizes missing core architectural requirements exponentially, floored at 0.25
    if missing_core_count > 0:
        d_core = max(0.25, round(0.70**missing_core_count, 3))
    else:
        d_core = 1.0

    return SkillGraphEvaluation(
        skill_score=round(final_skill_score, 4),
        d_core=d_core,
        matched_skills=matched_skills,
        transferred_skills=transferred_details,
        missing_skills=missing_skills,
        cold_start_applied=cold_start_applied,
    )
