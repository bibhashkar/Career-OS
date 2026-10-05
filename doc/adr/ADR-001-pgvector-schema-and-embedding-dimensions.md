# ADR-001: pgvector Schema and 1536-Dimensional Semantic Embeddings

## Status
Accepted

## Context
Career-OS requires matching candidate achievement blocks (`cv_block`) against job specifications dynamically. Keyword matching alone fails to capture domain nuances (e.g., "distributed fault tolerance" vs. "high availability systems"). We need a persistence mechanism capable of hybrid relational storage and cosine similarity vector retrieval.

## Decision
1. Utilize PostgreSQL with the `pgvector` extension.
2. Standardize vector dimensionality to **1536**, matching OpenAI `text-embedding-3-small` / Gemini embeddings compatible dimensions.
3. Index the `cv_block.embedding` column with an HNSW (Hierarchical Navigable Small World) index using `vector_cosine_ops` for low-latency approximate nearest neighbor (ANN) searches under concurrent loads.
4. Fall back to deterministic mock embeddings in local/test offline environments when external model API keys are absent.

## Consequences
- **Positive:** Single datastore for relational entities (`user_profile`, `job_listing`) and semantic embeddings eliminates dual-write synchronization issues. HNSW index delivers sub-millisecond similarity lookups.
- **Negative:** Requires PostgreSQL container with pre-installed `pgvector` binaries (`pgvector/pgvector:pg16`).
