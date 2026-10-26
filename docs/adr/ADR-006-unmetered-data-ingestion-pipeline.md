# ADR-006: Unmetered Anti-Fragile Data Ingestion and Synchronization Pipeline

## Status
Accepted

## Context
Career-OS originally relied on paid, rate-limited third-party APIs (JSearch, Exa, Apollo) for job search and company intelligence. In local development or during high search volume, these metered APIs quickly depleted budgets, fell back to unlabelled mock data, or caused pipeline starvation for downstream LangGraph agents (Hunter, ATS, Tailor, Coach). Furthermore, commercial aggregators often returned stale or closed postings with fabricated technical requirements.

## Decision
1. **Sync-then-Search Architecture:** Transitioned from Query-time dorking to background synchronization of official public ATS endpoints (Greenhouse, Lever, Ashby). Search operates locally against PostgreSQL via indexed filtering, full-text search, and semantic ranking, incurring zero external quota per search query.
2. **Autonomous Board Discovery & Snowballing:** Automated ATS board discovery via candidate slug probing and aggregator apply URL extraction. Discovered boards are validated against company domains before registration in `ats_board`.
3. **Hybrid Grounded Extraction & Crawl-Time Requirements:** Structured skills, functional role family, seniority level, and core dealbreakers are extracted deterministically at crawl time in `BoardSyncService._upsert_job` and persisted in `JobListing.ats_requirements` (supported by `IngestionTaskType.EXTRACT_REQUIREMENTS`), eliminating run-time extraction overhead during matching queries.
4. **Provenance and Auditability:** Added `data_origin` (`live`, `manual`, `demo`, `legacy`), `source_confidence` (`high`, `medium`, `low`), and `field_provenance` audit logs to `job_listing` and `company_dossier`. Unknown fields remain `null`/empty rather than fabricated.
5. **Secondary Verification:** Cross-checks shortlisted jobs against secondary aggregators without overwriting authoritative ATS data. Discrepancies are logged in `verification` with a 7-day TTL cache.
6. **Security Boundaries:** Enforced 'parse, don't fetch' for known ATS URLs and strict SSRF / DNS-rebinding protection (`validate_and_guard_url`) for arbitrary URLs. Untrusted job descriptions are sanitized server-side.
7. **Rate Ledger & Circuit Breaker:** Implemented atomic PostgreSQL budget reservation (`PersistentBudgetLedger`) and provider circuit breakers (`CircuitBreaker`) to prevent quota exhaustion and gracefully handle upstream drift.

---

## Evolution Note (ADR-009)
As formalized in [**ADR-009**](ADR-009-deep-candidate-intelligence-and-completeness-engine.md), all ingested jobs now receive section-aware required vs. preferred skill parsing and canonical functional family classification (`engineering`, `data_ai`, `sales_gtm`, `marketing`, `people_hr`, `legal_finance`, `operations`) during the crawl phase. This guarantees that non-technical roles do not leak into technical streams, while maintaining sub-15ms Stage 1 retrieval latency.

## Consequences
- **Positive:** Unmetered, highly accurate job discovery; resilient to external API outages and rate limits; honest provenance tracking across frontend and agent layers.
- **Negative:** Big tech employers without public ATS APIs require per-company adapters or aggregator fallback; background worker daemon required for periodic sync.
