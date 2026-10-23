"""
Information Retrieval (IR) Evaluation Metric Harness.

Implements standard ranking and quality evaluation metrics per MATCHING_ENGINE_SPEC:
- NDCG@10: Normalized Discounted Cumulative Gain at rank 10
- MRR: Mean Reciprocal Rank (position of first item with relevance >= 2)
- Precision@5: Proportion of relevant items in the top 5
- Gate Leakage: Rate of hard gate violations in top 20
- Latency: p50, p95, p99 latency benchmarking
"""

import math
from dataclasses import dataclass, field
from typing import Any


def compute_dcg_at_k(relevance_scores: list[int], k: int = 10) -> float:
    """
    Compute Discounted Cumulative Gain at rank k using 2^rel - 1 gain formulation.

    DCG@k = sum_{i=1}^k (2^r_i - 1) / log2(i + 1)
    """
    bounded = relevance_scores[:k]
    dcg = 0.0
    for idx, score in enumerate(bounded, start=1):
        if score > 0:
            gain = (2**score) - 1.0
            discount = math.log2(idx + 1)
            dcg += gain / discount
    return dcg


def compute_idcg_at_k(ideal_scores: list[int], k: int = 10) -> float:
    """
    Compute Ideal Discounted Cumulative Gain at rank k.
    """
    sorted_ideal = sorted(ideal_scores, reverse=True)
    return compute_dcg_at_k(sorted_ideal, k=k)


def compute_ndcg_at_k(
    retrieved_ids: list[str],
    ground_truth: dict[str, int],
    k: int = 10,
) -> float:
    """
    Compute Normalized Discounted Cumulative Gain at rank k.

    NDCG@k = DCG@k / IDCG@k in [0.0, 1.0]
    """
    if not retrieved_ids or not ground_truth:
        return 0.0

    retrieved_scores = [ground_truth.get(jid, 0) for jid in retrieved_ids[:k]]
    all_ideal_scores = [score for score in ground_truth.values() if score > 0]

    if not all_ideal_scores:
        return 0.0

    dcg = compute_dcg_at_k(retrieved_scores, k=k)
    idcg = compute_idcg_at_k(all_ideal_scores, k=k)

    if idcg <= 0.0:
        return 0.0

    return min(1.0, max(0.0, dcg / idcg))


def compute_reciprocal_rank(
    retrieved_ids: list[str],
    ground_truth: dict[str, int],
    threshold: int = 2,
) -> float:
    """
    Compute Reciprocal Rank: 1 / rank of first item with relevance >= threshold.
    """
    for rank, jid in enumerate(retrieved_ids, start=1):
        if ground_truth.get(jid, 0) >= threshold:
            return 1.0 / rank
    return 0.0


def compute_precision_at_k(
    retrieved_ids: list[str],
    ground_truth: dict[str, int],
    k: int = 5,
    threshold: int = 2,
) -> float:
    """
    Compute Precision at rank k: fraction of top k items with relevance >= threshold.
    """
    bounded = retrieved_ids[:k]
    if not bounded:
        return 0.0

    relevant_count = sum(1 for jid in bounded if ground_truth.get(jid, 0) >= threshold)
    return relevant_count / float(len(bounded))


def compute_gate_leakage(
    retrieved_jobs: list[dict[str, Any]],
    candidate_visa: str,
    candidate_locations: list[str],
    candidate_remote_pref: str,
    k: int = 20,
) -> float:
    """
    Compute Gate Leakage: fraction of jobs in top k that violate hard gates.

    Violations:
      - Candidate requires visa sponsorship and job explicitly declares 'no'.
      - Candidate requires remote but job is strictly on-site in non-commuting city.
    """
    bounded = retrieved_jobs[:k]
    if not bounded:
        return 0.0

    requires_visa = candidate_visa.strip().lower() in {
        "h-1b",
        "f-1 opt",
        "requires_sponsorship",
        "requires sponsorship",
    }
    cand_pref_remote = candidate_remote_pref.strip().lower() == "remote"

    violations = 0
    for j in bounded:
        j_visa = str(j.get("visa_sponsorship", "") or "").strip().lower()
        if requires_visa and j_visa == "no":
            violations += 1
            continue

        workplace = str(j.get("workplace_type", "") or "").strip().lower()
        loc = str(j.get("raw_location", "") or "").strip().lower()

        if cand_pref_remote and workplace == "on_site":
            matched_loc = any(
                cloc.lower() in loc
                for cloc in candidate_locations
                if cloc.lower() != "remote"
            )
            if not matched_loc:
                violations += 1

    return violations / float(len(bounded))


@dataclass
class CandidateEvalMetrics:
    """Evaluation metrics for a single candidate evaluation run."""

    candidate_id: str
    candidate_name: str
    ndcg_at_10: float
    reciprocal_rank: float
    precision_at_5: float
    gate_leakage: float
    latency_ms: float
    top_retrieved_ids: list[str] = field(default_factory=list)


@dataclass
class IRBenchmarkSummary:
    """Aggregated Information Retrieval evaluation summary across all candidates."""

    total_candidates: int
    total_jobs: int
    mean_ndcg_at_10: float
    mean_mrr: float
    mean_precision_at_5: float
    gate_leakage_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    candidate_metrics: list[CandidateEvalMetrics] = field(default_factory=list)


def evaluate_candidate_ranking(
    candidate_id: str,
    candidate_name: str,
    ranked_jobs: list[tuple[str, float, dict[str, Any]]],
    ground_truth: dict[str, int],
    candidate_visa: str,
    candidate_locations: list[str],
    candidate_remote_pref: str,
    latency_ms: float = 0.0,
) -> CandidateEvalMetrics:
    """
    Calculate full IR metric breakdown for a candidate run.

    ranked_jobs: List of (job_id, match_score, job_dict)
        sorted by match_score descending.
    """
    retrieved_ids = [r[0] for r in ranked_jobs]
    retrieved_job_dicts = [r[2] for r in ranked_jobs]

    ndcg = compute_ndcg_at_k(retrieved_ids, ground_truth, k=10)
    rr = compute_reciprocal_rank(retrieved_ids, ground_truth, threshold=2)
    p5 = compute_precision_at_k(retrieved_ids, ground_truth, k=5, threshold=2)
    leakage = compute_gate_leakage(
        retrieved_job_dicts,
        candidate_visa=candidate_visa,
        candidate_locations=candidate_locations,
        candidate_remote_pref=candidate_remote_pref,
        k=20,
    )

    return CandidateEvalMetrics(
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        ndcg_at_10=round(ndcg, 4),
        reciprocal_rank=round(rr, 4),
        precision_at_5=round(p5, 4),
        gate_leakage=round(leakage, 4),
        latency_ms=round(latency_ms, 2),
        top_retrieved_ids=retrieved_ids[:10],
    )


def aggregate_benchmark_metrics(
    candidate_metrics: list[CandidateEvalMetrics],
    total_jobs: int,
) -> IRBenchmarkSummary:
    """
    Aggregate metrics across candidate population into percentiles and means.
    """
    if not candidate_metrics:
        return IRBenchmarkSummary(
            total_candidates=0,
            total_jobs=total_jobs,
            mean_ndcg_at_10=0.0,
            mean_mrr=0.0,
            mean_precision_at_5=0.0,
            gate_leakage_rate=0.0,
            latency_p50_ms=0.0,
            latency_p95_ms=0.0,
            latency_p99_ms=0.0,
        )

    n = len(candidate_metrics)
    mean_ndcg = sum(m.ndcg_at_10 for m in candidate_metrics) / n
    mean_mrr = sum(m.reciprocal_rank for m in candidate_metrics) / n
    mean_p5 = sum(m.precision_at_5 for m in candidate_metrics) / n
    mean_leakage = sum(m.gate_leakage for m in candidate_metrics) / n

    latencies = sorted(m.latency_ms for m in candidate_metrics)

    def _percentile(data: list[float], pct: float) -> float:
        if not data:
            return 0.0
        idx = int(math.ceil(pct * len(data))) - 1
        idx = max(0, min(len(data) - 1, idx))
        return data[idx]

    return IRBenchmarkSummary(
        total_candidates=n,
        total_jobs=total_jobs,
        mean_ndcg_at_10=round(mean_ndcg, 4),
        mean_mrr=round(mean_mrr, 4),
        mean_precision_at_5=round(mean_p5, 4),
        gate_leakage_rate=round(mean_leakage, 4),
        latency_p50_ms=round(_percentile(latencies, 0.50), 2),
        latency_p95_ms=round(_percentile(latencies, 0.95), 2),
        latency_p99_ms=round(_percentile(latencies, 0.99), 2),
        candidate_metrics=candidate_metrics,
    )
