# Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite

**Document Version:** 2.0.0  
**Target Systems:** `backend/app/services/matching.py`, `backend/app/ingestion/`, `backend/app/models/`, `backend/tests/eval/`  
**Execution Target:** Antigravity AIs & Autonomous Subagents
 
---

## 1. Executive Summary & Problem Analysis

This specification defines the architectural upgrades required to transition the Career-OS candidate-job matching engine from a heuristic baseline to an industrial-grade, information-retrieval (IR) recommendation engine.

### 1.1 Flaws in Baseline Matching Architecture
1. **$S_{semantic}$ Double-Counting Bug:** The baseline formula defines $S_{semantic} = \max(0.2, 0.6 \cdot S_{skills} + 0.4 \cdot \text{RoleMatchRatio})$. It never computes vector cosine similarity. Consequently, exact keyword matching ($S_{skills}$) is counted twice, controlling $45%$ of the total candidate score, while 1536-dimensional `pgvector` embeddings contribute $0%$ to Stage 2 ranking.
2. **Stage 1 Recency Starvation:** Ordering Stage 1 candidates strictly by `created_at DESC LIMIT 250` causes older, highly compatible listings to be dropped when crawler volume spikes, starving Stage 2 of valid candidates.
3. **Job-Invariant Factor Collapse:** Candidate prestige ($S_{prestige}$) and achievement honors ($S_{achievement}$) evaluate to identical static constants across all jobs in a single run, adding a dead $20%$ offset with zero ranking discrimination.
4. **Symmetric Equivalence Errors:** Undirected technology equivalence (e.g., `Docker == Kubernetes`) fails to capture directional competency (Kubernetes implies container mastery; Docker does not imply container orchestration mastery).
5. **Uniform Skill Weighting (1/N Fallacy):** Core requirements, preferred bonuses, and boilerplate tools are weighted identically, allowing keyword-stuffed resumes to outrank production-proven specialists.

---

## 2. Gap Analysis: System Requirements Previously Missing

1. **Compensation Normalization ($S_{comp}$):** Normalizes all salary ranges to annualized USD base salary, using DOL/USCIS H-1B Prevailing Wage data for jobs lacking compensation details. Penalizes jobs below target exponentially.
2. **Cross-ATS Deduplication via Fingerprinting:** Computes a `SHA256(company_slug + normalized_title + location_code)` hash to merge duplicate postings across Greenhouse, Lever, Ashby, Workable, and SmartRecruiters.
3. **Implicit Feedback Ingestion:** Captures clicks, tailor generations, and interview simulator starts to update factor weights dynamically via Thompson Sampling.
4. **Cold-Start & Sparse Profile Handling:** Activates the Implied Skills DAG when candidates have fewer than 3 atomic `op_vector` chunks, applying neutral 0.65 priors to prevent false rejections.
5. **Sub-50ms Latency SLA:** Stage 1 relational filter <= 15ms;; Stage 2 multi-factor reranking <= 30ms; uses in-memory SIMD dot products for Top-3 Block cosine similarity.

---

## 3. Upgraded Matching Engine Specification

### 3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF)
Replaces recency ordering with a PG GIN Skill Index + HNSW Vector Index + Recency fusion function that guarantees the 250 candidates retrieved are the most relevant jobs across the entire corpus.

### 3.2 Stage 2: Unified Multi-Factor Reranking Equation

$$P(\text{Match}) = (G_{\text{prob}} \cdot D_{\text{core}}) \times \Big[
	0.25 \cdot S_{\text{skills}} +
	0.25 \cdot S_{\text{semantic}} +
	0.15 \cdot S_{\text{seniority}} +
	0.15 \cdot S_{\text{context}} +
	0.10 \cdot S_{\text{comp}} +
	0.10 \cdot S_{\text{freshness}} \Big]$$

#### Context & Domain Alignment Blending ($S_{\text{context}}$)
To eliminate vertical domain blindness in heavily regulated sectors (HealthTech, FinTech, Defense), the $0.15$ context slice unifies company archetype and explicit industry domain mastery regulated by the job's Domain Strictness Tier ($\beta_{\text{domain}} \in [0.0, 1.0]$):

$$S_{\text{context}} = (1 - \beta_{\text{domain}}) \cdot S_{\text{archetype}} + \beta_{\text{domain}} \cdot S_{\text{domain}}$$

Where:
- Candidate Domain Profile $\vec{D}_{\text{cand}}$ is computed from verified `cv_block` history with recency decay $\gamma = 0.90$.
- Domain Match Score: $S_{\text{domain}} = (\vec{D}_{\text{cand}} \cdot \vec{D}_{\text{job}}) \times \text{TenureBonus}(\text{YoE}_{\text{domain}})$
- Piecewise saturating tenure curve:
  $$\text{TenureBonus}(\text{YoE}) = \min(1.0, \; 0.50 + 0.10 \cdot \min(\text{YoE}, 5) + 0.02 \cdot \max(0, \text{YoE} - 5))$$
- Strictness Tiers:
  - $\beta = 1.0$ (Strict/Regulated): Explicit mandates or deep regulatory protocols (`EDI 837/835`, `HL7/FHIR`, `DICOM`, `PCI-DSS`, `FedRAMP`).
  - $\beta = 0.5$ (Preferred): Industry-specific roles without hard regulatory prerequisites.
  - $\beta = 0.0$ (Domain Agnostic): General SaaS or commodity tech where $S_{\text{context}} = S_{\text{archetype}}$.

---

## 4. Evaluation Toolkit & Verification Suite

Module directory: `backend/tests/eval/`

|| Metric | Production Target | Scope ||
----------------------------------------------------------------------
|| NDCG@10 | >= 0.88 | Ranking accurcy using 4-point graded relevance ||
|| MRR | >= 0.92 | Position of first high-quality match (relevance >= 2) ||
|| Precision@5 | >= 0.80 | Verifies 4 fiveth of visible jobs are production viable ||
|| Gate Leakage (L_gate) | 0.00% || Zero tolerance for visa or location disqualification in top 20 ||
|| p95 Latency | < 45ms || Stage 1 + Stage 2 total execution time ||

---

## 5. Implementation Roadmap

1. Step 1: Adding GIN and HNSW indexes, salary normalization, and content fingerprinting to cache and job_listing tables via pure SQL migration (`db/migrations/0002_matching_engine_v2_schema.sql` & `db/migrate.py`).
2. Step 2: Creating backend/app/services/skill_graph.py with asymmetric transfer matrices, canonical alias normalizer, IDF specificity weighting, and cold-start DAG expansion.
3. Step 3: Refactoring Stage 1 (Hybrid RRF) and Stage 2 (Multi-Factor Reranking) functions in backend/app/services/matching.py.
4. Step 4: Generating the 25-candidate x 500-job golden benchmark dataset in backend/tests/eval/datasets/.
5. Step 5: Enforcing NDCG@10 >= 0.88 and 0% gate leakage in backend/tests/test_ranking_regression.py.
