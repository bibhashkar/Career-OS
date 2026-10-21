"""
Unit tests for Asymmetric Skill Graph, Directional Transfer Matrix, and IDF Weights.
"""

import pytest

from app.services.skill_graph import (
    compute_asymmetric_skill_score,
    expand_implied_skills,
    get_skill_idf_weight,
    get_transfer_weight,
    normalize_skill,
)


def test_normalize_skill_aliases() -> None:
    """Verify canonical normalization of common aliases and surface variations."""
    assert normalize_skill("k8s") == "kubernetes"
    assert normalize_skill("K8S") == "kubernetes"
    assert normalize_skill("kube") == "kubernetes"
    assert normalize_skill("golang") == "go"
    assert normalize_skill("Go") == "go"
    assert normalize_skill("postgres") == "postgresql"
    assert normalize_skill("PostgreSQL") == "postgresql"
    assert normalize_skill("psql") == "postgresql"
    assert normalize_skill("nodejs") == "node.js"
    assert normalize_skill("node.js") == "node.js"
    assert normalize_skill("reactjs") == "react"
    assert normalize_skill("vuejs") == "vue"
    assert normalize_skill("nextjs") == "next.js"
    assert normalize_skill("ts") == "typescript"
    assert normalize_skill("py") == "python"
    assert normalize_skill("python3") == "python"
    assert normalize_skill("aws cloud") == "aws"
    assert normalize_skill("amazon web services") == "aws"
    assert normalize_skill("google cloud platform") == "gcp"
    assert normalize_skill("microsoft azure") == "azure"
    assert normalize_skill("torch") == "pytorch"
    assert normalize_skill("") == ""


def test_asymmetric_directionality() -> None:
    """Verify that skill transfers are directional and non-symmetric."""
    # 1. Kubernetes implies Docker mastery, but Docker DOES NOT imply K8s orchestration
    k8s_to_docker = get_transfer_weight("kubernetes", "docker")
    docker_to_k8s = get_transfer_weight("docker", "kubernetes")
    assert k8s_to_docker >= 0.85
    assert docker_to_k8s <= 0.40
    assert k8s_to_docker > docker_to_k8s

    # 2. FastAPI implies Python, but general Python does not imply async web framework
    fastapi_to_py = get_transfer_weight("fastapi", "python")
    py_to_fastapi = get_transfer_weight("python", "fastapi")
    assert fastapi_to_py >= 0.90
    assert py_to_fastapi <= 0.40
    assert fastapi_to_py > py_to_fastapi

    # 3. Kafka implies message queuing, but RabbitMQ does not imply partitioned stream
    kafka_to_rabbit = get_transfer_weight("kafka", "rabbitmq")
    rabbit_to_kafka = get_transfer_weight("rabbitmq", "kafka")
    assert kafka_to_rabbit >= 0.75
    assert rabbit_to_kafka <= 0.65
    assert kafka_to_rabbit > rabbit_to_kafka

    # 4. Next.js implies React, but React only gives partial ramp-up to SSR
    next_to_react = get_transfer_weight("next.js", "react")
    react_to_next = get_transfer_weight("react", "next.js")
    assert next_to_react >= 0.90
    assert react_to_next <= 0.70
    assert next_to_react > react_to_next


def test_peer_lateral_transfers() -> None:
    """Verify peer technologies in the same domain transfer with reasonable parity."""
    # Cloud providers
    assert get_transfer_weight("aws", "gcp") == 0.75
    assert get_transfer_weight("gcp", "aws") == 0.75
    assert get_transfer_weight("aws", "azure") == 0.75

    # Relational databases
    assert get_transfer_weight("postgresql", "mysql") == 0.85
    assert get_transfer_weight("mysql", "postgresql") == 0.85

    # Deep learning frameworks
    assert get_transfer_weight("pytorch", "tensorflow") == 0.80
    assert get_transfer_weight("tensorflow", "pytorch") == 0.80


def test_two_hop_transitive_decay() -> None:
    """Verify multi-hop transitive transfer carries appropriate decay."""
    # Helm -> Kubernetes (0.85), Kubernetes -> Docker (0.90)
    # Transitive: 0.85 * 0.90 * 0.85 = 0.6503
    helm_to_docker = get_transfer_weight("helm", "docker")
    assert helm_to_docker >= 0.60
    assert helm_to_docker < 0.85

    # Tokio -> Rust (0.95), Rust -> Systems Programming (0.95)
    tokio_to_sys = get_transfer_weight("tokio", "systems programming")
    assert tokio_to_sys >= 0.70


def test_idf_specificity_weighting() -> None:
    """Verify rare and systems skills carry higher IDF weights than boilerplate."""
    rust_w = get_skill_idf_weight("rust")
    cuda_w = get_skill_idf_weight("cuda")
    k8s_w = get_skill_idf_weight("kubernetes")
    py_w = get_skill_idf_weight("python")
    git_w = get_skill_idf_weight("git")
    agile_w = get_skill_idf_weight("agile")
    json_w = get_skill_idf_weight("json")

    assert rust_w > py_w > git_w
    assert cuda_w > 2.0
    assert k8s_w >= 1.8
    assert git_w <= 0.6
    assert agile_w <= 0.5
    assert json_w <= 0.5

    # Core skill multiplier
    core_k8s_w = get_skill_idf_weight("kubernetes", is_core=True)
    assert core_k8s_w == round(k8s_w * 1.25, 3)


def test_compute_asymmetric_skill_score_defeats_keyword_stuffing() -> None:
    """
    Demonstrate that matching core high-IDF skills outscores matching multiple
    commodity skills, defeating the 1/N keyword-stuffing fallacy.
    """
    job_skills = ["kubernetes", "git", "json", "agile"]

    # Candidate A: Expert in Kubernetes, but didn't list boilerplate (git, json, agile)
    candidate_a_skills = {"kubernetes"}
    eval_a = compute_asymmetric_skill_score(candidate_a_skills, job_skills)

    # Candidate B: Keyword stuffer who lists commodity tools, but lacks Kubernetes
    candidate_b_skills = {"git", "json", "agile"}
    eval_b = compute_asymmetric_skill_score(candidate_b_skills, job_skills)

    # Candidate A should outscore Candidate B because Kubernetes carries weight 1.9
    # while git(0.5) + json(0.4) + agile(0.4) sum to only 1.3
    assert eval_a.skill_score > eval_b.skill_score
    assert "kubernetes" in eval_a.matched_skills
    assert "kubernetes" in eval_b.missing_skills
    # Candidate B is penalized by core dealbreaker D_core
    assert eval_b.d_core < 1.0


def test_expand_implied_skills() -> None:
    """Verify implied skills DAG expansion for cold-start candidates."""
    skills = {"fastapi", "kubernetes", "next.js"}
    expanded = expand_implied_skills(skills, min_transfer=0.85)

    assert "fastapi" in expanded
    assert "python" in expanded  # Implied by FastAPI (0.95)
    assert "kubernetes" in expanded
    assert "docker" in expanded  # Implied by Kubernetes (0.90)
    assert "next.js" in expanded
    assert "react" in expanded  # Implied by Next.js (0.95)
    assert "javascript" in expanded  # Implied by Next.js (0.95)


def test_cold_start_handling() -> None:
    """
    Verify sparse profile with < 3 CV blocks activates cold-start expansion
    and neutral prior floor.
    """
    candidate_skills = {"fastapi"}
    job_skills = ["python", "rest api"]

    # Candidate with only 1 CV block
    eval_sparse = compute_asymmetric_skill_score(
        candidate_skills,
        job_skills,
        cv_block_count=1,
    )
    assert eval_sparse.cold_start_applied is True
    assert "python" in eval_sparse.matched_skills
    assert eval_sparse.skill_score >= 0.85

    # Empty job skills fallback
    eval_empty = compute_asymmetric_skill_score(candidate_skills, [])
    assert eval_empty.skill_score == 0.70
    assert eval_empty.d_core == 1.0


def test_core_dealbreaker_penalty() -> None:
    """Verify missing non-negotiable core skills applies exponential D_core penalty."""
    job_skills = ["rust", "langgraph", "git"]
    core_job_skills = ["rust", "langgraph"]

    # Candidate has zero systems or agentic AI background
    cand_skills = {"python", "git"}
    evaluation = compute_asymmetric_skill_score(
        cand_skills,
        job_skills,
        core_job_skills=core_job_skills,
    )

    # Two missing core skills: D_core = 0.70 * 0.70 = 0.49
    assert evaluation.d_core == pytest.approx(0.49, rel=1e-2)
    assert "rust" in evaluation.missing_skills
    assert "langgraph" in evaluation.missing_skills

    # Candidate with one missing core skill (has Rust, lacks LangGraph)
    cand_one_core = {"rust", "git"}
    eval_one = compute_asymmetric_skill_score(
        cand_one_core,
        job_skills,
        core_job_skills=core_job_skills,
    )
    assert eval_one.d_core == pytest.approx(0.70, rel=1e-2)
    assert "langgraph" in eval_one.missing_skills

    # Candidate with all core skills
    cand_all_core = {"rust", "langgraph", "git"}
    eval_all = compute_asymmetric_skill_score(
        cand_all_core,
        job_skills,
        core_job_skills=core_job_skills,
    )
    assert eval_all.d_core == 1.0
