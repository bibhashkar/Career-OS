"""High-Probability Matching & Fault-Tolerant Ranking Regression Suite.

Validates ADR-008 and Master Spec production IR targets:
1. NDCG@10 >= 0.88
2. MRR >= 0.92
3. Precision@5 >= 0.80
4. Gate Leakage == 0.00%
5. Stage 2 Reranker p95 Latency < 45.0ms (50 pre-filtered jobs)
6. Regulated Domain Prioritization: Candidate with vertical domain mastery scores
   >= 12% higher than out-of-domain peer on strict vertical postings.
"""

import json
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.agents.tools.embeddings import generate_deterministic_embedding
from app.models.cv_block import CVBlock
from app.models.job_listing import JobListing
from app.models.user_account import CandidatePersona, UserAccount
from app.services.matching import calculate_match_upgraded
from tests.eval.eval_harness import (
    IRBenchmarkSummary,
    aggregate_benchmark_metrics,
    evaluate_candidate_ranking,
)


@pytest.fixture(scope="module")
def golden_benchmark_data() -> dict[str, Any]:
    with open("backend/tests/eval/datasets/matching_golden_benchmark.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def preloaded_jobs(
    golden_benchmark_data: dict[str, Any],
) -> list[tuple[str, JobListing, dict[str, Any]]]:
    raw_jobs = golden_benchmark_data["jobs"]
    job_objs = []
    for j in raw_jobs:
        posted = datetime.now(UTC) - timedelta(days=j.get("age_days", 5))
        job_text = f"{j['title']} {j.get('raw_description', '')}"
        emb = generate_deterministic_embedding(job_text)
        jl = JobListing(
            id=uuid.uuid4(),
            title=j["title"],
            company_name=j["company_name"],
            industry=j.get("industry"),
            industry_vertical=j.get("industry_vertical"),
            domain_strictness=j.get("domain_strictness", 0.5),
            raw_location=j.get("raw_location"),
            workplace_type=j.get("workplace_type"),
            salary_range=j.get("salary_range"),
            salary_min=j.get("salary_min"),
            salary_max=j.get("salary_max"),
            visa_sponsorship=j.get("visa_sponsorship"),
            raw_description=j.get("raw_description"),
            ats_requirements=j.get("ats_requirements", {}),
            posted_at=posted,
            embedding=emb,
        )
        job_objs.append((j["job_id"], jl, j))
    return job_objs


@pytest.fixture(scope="module")
def benchmark_evaluation_results(
    golden_benchmark_data: dict[str, Any],
    preloaded_jobs: list[tuple[str, JobListing, dict[str, Any]]],
) -> IRBenchmarkSummary:
    candidates = golden_benchmark_data["candidates"]
    ground_truth = golden_benchmark_data["ground_truth"]
    candidate_metrics = []

    for cand in candidates:
        cand_id = cand["id"]
        persona = CandidatePersona(
            name=cand["name"],
            headline=cand["headline"],
            years_experience=cand["years_experience"],
            seniority_level=cand["seniority"],
            target_roles=cand["target_roles"],
            min_salary=cand["min_salary"],
        )
        blocks = []
        for b in cand["blocks"]:
            b_text = f"{b['title']} {b.get('content', '')}"
            b_emb = generate_deterministic_embedding(b_text)
            blocks.append(
                CVBlock(
                    title=b["title"],
                    organization=b["org"],
                    content=b["content"],
                    industry_tags=b["tags"],
                    metrics=b.get("metrics", {}),
                    skills=b.get("skills", []),
                    embedding=b_emb,
                )
            )
        account = UserAccount(
            visa_status=cand["visa_status"],
            preferred_locations=cand["locations"],
            remote_preference=cand["remote_pref"],
        )
        cand_skills = set(cand["skills"])

        t0 = time.perf_counter()
        scored_jobs = []
        for jid, jl, jdict in preloaded_jobs:
            score, _ = calculate_match_upgraded(
                persona=persona,
                job=jl,
                blocks=blocks,
                persona_skills=cand_skills,
                account=account,
            )
            scored_jobs.append((jid, score, jdict))

        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        metrics = evaluate_candidate_ranking(
            candidate_id=cand_id,
            candidate_name=cand["name"],
            ranked_jobs=scored_jobs,
            ground_truth=ground_truth[cand_id],
            candidate_visa=cand["visa_status"],
            candidate_locations=cand["locations"],
            candidate_remote_pref=cand["remote_pref"],
            latency_ms=latency_ms,
        )
        candidate_metrics.append(metrics)

    return aggregate_benchmark_metrics(candidate_metrics, len(preloaded_jobs))


def test_ranking_regression_ndcg_at_10(
    benchmark_evaluation_results: IRBenchmarkSummary,
) -> None:
    """Production SLA: NDCG@10 >= 0.88 across all candidate archetypes."""
    actual_ndcg = benchmark_evaluation_results.mean_ndcg_at_10
    assert actual_ndcg >= 0.88, f"Mean NDCG@10 failed SLA: {actual_ndcg:.4f} < 0.88"


def test_ranking_regression_mrr(
    benchmark_evaluation_results: IRBenchmarkSummary,
) -> None:
    """Production SLA: Mean Reciprocal Rank (MRR) >= 0.92."""
    actual_mrr = benchmark_evaluation_results.mean_mrr
    assert actual_mrr >= 0.92, f"MRR failed SLA: {actual_mrr:.4f} < 0.92"


def test_ranking_regression_precision_at_5(
    benchmark_evaluation_results: IRBenchmarkSummary,
) -> None:
    """Production SLA: Precision@5 >= 0.80."""
    actual_p5 = benchmark_evaluation_results.mean_precision_at_5
    assert actual_p5 >= 0.80, f"Precision@5 failed SLA: {actual_p5:.4f} < 0.80"


def test_ranking_regression_zero_gate_leakage(
    benchmark_evaluation_results: IRBenchmarkSummary,
) -> None:
    """Production SLA: Gate Leakage == 0.00%."""
    leakage = benchmark_evaluation_results.gate_leakage_rate
    assert leakage == 0.00, f"Gate leakage violation detected: {leakage:.4%}"


def test_ranking_regression_stage2_latency(
    preloaded_jobs: list[tuple[str, JobListing, dict[str, Any]]],
) -> None:
    """Production SLA: Stage 2 Reranker p95 latency < 45.0ms for 50 jobs."""
    top_50_jobs = preloaded_jobs[:50]
    persona = CandidatePersona(
        name="Latency Benchmark Candidate",
        headline="Senior Systems Engineer",
        years_experience=7,
        seniority_level="senior",
        target_roles=["Senior Backend Engineer"],
        min_salary=160000,
    )
    blocks = [
        CVBlock(
            title="Senior Backend Engineer",
            organization="Datadog",
            content="Built scalable distributed microservices in Go and Kubernetes.",
            industry_tags=["devtools"],
            metrics={"qps": 50000},
            skills=["Go", "Kubernetes", "Docker", "AWS"],
            embedding=generate_deterministic_embedding(
                "Senior Backend Engineer Datadog"
            ),
        )
    ]
    account = UserAccount(
        visa_status="Citizen",
        preferred_locations=["Remote"],
        remote_preference="remote",
    )
    cand_skills = {"Go", "Kubernetes", "Docker", "AWS", "Python"}

    latencies: list[float] = []
    # Warmup
    for _, jl, _ in top_50_jobs:
        calculate_match_upgraded(persona, jl, blocks, cand_skills, account)

    # 10 trial runs of 50 jobs
    for _ in range(10):
        t0 = time.perf_counter()
        for _, jl, _ in top_50_jobs:
            calculate_match_upgraded(persona, jl, blocks, cand_skills, account)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95)]
    assert (
        p95_latency < 45.0
    ), f"Stage 2 p95 latency for 50 jobs exceeded 45ms: {p95_latency:.2f}ms"


def test_regulated_domain_prioritization() -> None:
    """Domain Alignment SLA:

    A candidate with 10 years of verified HealthTech domain tenure (HIPAA, FHIR,
    EDI 837) must score >= 12% higher than an equally senior candidate with 10
    years of Gaming experience when matching against a strict HealthTech
    requisition (beta_domain = 1.0).
    """
    health_job = JobListing(
        id=uuid.uuid4(),
        title="Senior Health Systems Platform Engineer",
        company_name="Optum",
        industry="healthtech",
        industry_vertical="healthtech",
        domain_strictness=1.0,
        raw_location="Remote",
        workplace_type="remote",
        salary_range="$170k - $210k",
        salary_min=170000,
        salary_max=210000,
        visa_sponsorship="yes",
        raw_description=(
            "Core clinical claims engine. Requires HIPAA, FHIR, and EDI 837 experience."
        ),
        ats_requirements={
            "hard_skills": [
                "Python",
                "PostgreSQL",
                "AWS",
                "HIPAA",
                "FHIR",
                "EDI 837",
                "Docker",
            ],
            "core_skills": ["HIPAA", "FHIR", "EDI 837"],
            "years_experience_min": 7,
            "seniority_level": "senior",
        },
        posted_at=datetime.now(UTC),
        embedding=generate_deterministic_embedding(
            "Senior Health Systems Platform Engineer Optum HIPAA FHIR EDI"
        ),
    )

    # Candidate A: 10 Years HealthTech Experience
    cand_a_persona = CandidatePersona(
        name="Elena Rostova",
        headline="Senior Healthcare Systems Architect",
        years_experience=10,
        seniority_level="senior",
        target_roles=["Senior Backend Engineer"],
        min_salary=160000,
    )
    cand_a_blocks = [
        CVBlock(
            title="Senior Healthcare Systems Architect",
            organization="Epic Systems",
            content="Built FHIR and EDI 837 clinical data pipelines under HIPAA.",
            industry_tags=["healthtech"],
            metrics={"duration_years": 10},
            skills=["Python", "PostgreSQL", "AWS", "HIPAA", "FHIR", "EDI 837"],
            embedding=generate_deterministic_embedding(
                "Senior Healthcare Systems Architect Epic Systems"
            ),
        )
    ]
    cand_a_account = UserAccount(
        visa_status="Citizen",
        preferred_locations=["Remote"],
        remote_preference="remote",
    )
    cand_a_skills = {
        "Python",
        "PostgreSQL",
        "AWS",
        "HIPAA",
        "FHIR",
        "EDI 837",
        "Docker",
    }

    # Candidate B: 10 Years Gaming Experience (Identical generic stack)
    cand_b_persona = CandidatePersona(
        name="Marcus Vance",
        headline="Senior Game Engine & Multiplayer Architect",
        years_experience=10,
        seniority_level="senior",
        target_roles=["Senior Backend Engineer"],
        min_salary=160000,
    )
    cand_b_blocks = [
        CVBlock(
            title="Senior Game Engine Architect",
            organization="Riot Games",
            content="Architected low-latency multiplayer game backend servers.",
            industry_tags=["gaming"],
            metrics={"duration_years": 10},
            skills=["Python", "PostgreSQL", "AWS", "Unreal Engine", "Multiplayer Game"],
            embedding=generate_deterministic_embedding(
                "Senior Game Engine Architect Riot Games"
            ),
        )
    ]
    cand_b_account = UserAccount(
        visa_status="Citizen",
        preferred_locations=["Remote"],
        remote_preference="remote",
    )
    cand_b_skills = {
        "Python",
        "PostgreSQL",
        "AWS",
        "Docker",
        "Unreal Engine",
        "Multiplayer Game",
    }

    score_a, breakdown_a = calculate_match_upgraded(
        cand_a_persona, health_job, cand_a_blocks, cand_a_skills, cand_a_account
    )
    score_b, breakdown_b = calculate_match_upgraded(
        cand_b_persona, health_job, cand_b_blocks, cand_b_skills, cand_b_account
    )

    diff_percentage = (score_a - score_b) * 100.0
    print(
        f"\nHealthTech Candidate Score: {score_a:.4f} "
        f"(Domain: {breakdown_a.domain_score:.2f})"
    )
    print(
        f"Gaming Candidate Score:     {score_b:.4f} "
        f"(Domain: {breakdown_b.domain_score:.2f})"
    )
    print(f"Score Separation:           {diff_percentage:.2f}%")

    assert (
        diff_percentage >= 12.0
    ), f"Domain alignment separation failed: {diff_percentage:.2f}% < 12.0%"
