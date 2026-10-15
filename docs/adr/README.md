# Architecture Decision Records (ADRs)

This directory maintains the historical log of significant architectural and design decisions made for Career-OS, structured according to Michael Nygard's Architecture Decision Record (ADR) format.

---

## ADR Index

| ADR ID | Title | Date | Status | Summary |
| :--- | :--- | :--- | :--- | :--- |
| [**ADR-001**](ADR-001-pgvector-schema-and-embedding-dimensions.md) | pgvector Schema and 1536-Dimensional Semantic Embeddings | 2026-10-05 | **Accepted** | Native PostgreSQL `pgvector` HNSW index for sub-millisecond cosine similarity on 1536-dim resume blocks. |
| [**ADR-002**](ADR-002-checkpointer-persistence-and-thread-namespacing.md) | Checkpointer Persistence and Thread Namespacing | 2026-10-05 | **Accepted** | `AsyncPostgresSaver` checkpointing for resumable, multi-turn WebSocket mock interviews keyed on `thread_id`. |
| [**ADR-003**](ADR-003-agent-graph-decomposition-and-ats-loop-guard.md) | Agent Graph Decomposition and ATS Loop Guard | 2026-10-05 | **Accepted** | Decoupled LangGraph multi-agent architecture with bounded cyclic revision guard (`MAX_REVISIONS = 3`). |
| [**ADR-004**](ADR-004-foreign-key-strict-restrict-deletion-policy.md) | Foreign Key Strict RESTRICT Deletion Policy | 2026-10-05 | **Accepted** | Enforce `ON DELETE RESTRICT` across relational entities to prevent accidental cascades on career history. |
| [**ADR-005**](ADR-005-llm-provider-abstraction-and-gemini-integration.md) | LLM Provider Abstraction and Google Gemini Integration | 2026-10-05 | **Accepted** | LangChain `ChatGoogleGenerativeAI` default model with hermetic mock fallbacks for offline testing. |
| [**ADR-006**](ADR-006-unmetered-data-ingestion-pipeline.md) | Unmetered Direct-to-ATS Data Ingestion Pipeline | 2026-10-09 | **Accepted** | Direct HTTP ingestion across 5 major public ATS engines (Greenhouse, Lever, Ashby, Workable, SmartRecruiters) and scaled 1,000+ catalog. |
| [**ADR-007**](ADR-007-candidate-modeling-multi-persona-and-ingestion.md) | Candidate Modeling, Multi-Modal Ingestion & Multi-Persona Architecture | 2026-10-15 | **Accepted** | Decoupled user account identity, Universal Persona with hybrid strengths, specialized career personas, and 5-tier STAR CV blocks. |
| [**ADR-008**](ADR-008-high-probability-job-matching-and-fault-tolerant-ranking.md) | High-Probability Job Matching, Two-Stage Retrieval & Fault-Tolerant Ranking | 2026-10-15 | **Accepted** | Two-stage Galene-inspired retrieval (Stage 1 SQL filter <15ms + Stage 2 precision reranker) with Bayesian uncertainty gating $G_{\text{prob}}$ and pedigree boosters. |

---

## Architectural Principles Enforced by ADRs

1. **Decoupled Architecture**: Presentation strictly in React; all agent workflows, orchestration, and LLM inference reside in FastAPI/LangGraph.
2. **Persistence Integrity**:
   - Short-term: `PostgresSaver` for thread state checkpointing.
   - Long-term: Relational PostgreSQL with strict foreign key referential integrity (`ON DELETE RESTRICT`).
   - Semantic: Native PostgreSQL `pgvector` with HNSW cosine indexes.
3. **Hermetic Test Isolation**: All agent nodes and embedding pipelines run 100% offline in CI environments via deterministic projection.
4. **Single-Source Schema Management**: Pure sequential SQL migrations in `db/migrations/0001_initial_schema.sql` tracked via SHA-256 verification runner.

