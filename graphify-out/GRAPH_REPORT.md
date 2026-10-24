# Graph Report - career-os  (2026-10-23)

## Corpus Check
- 205 files · ~205,879 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .conf 1)

## Summary
- 2191 nodes · 4812 edges · 143 communities (109 shown, 34 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 424 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0c33996e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- candidates.py
- models.py
- typing
- sqlalchemy
- adapters/ats.py
- post
- migrate.py
- diagnostics.py
- test_matching.py
- BaseModel
- embeddings.py
- test_coach_llm.py
- provider.py
- test_cv_export.py
- api.py
- Evolution: Matching Engine v2.0 (Industrial-Grade Hybrid Retrieval)
- package.json
- Settings
- company_intel_provider.py
- AgentState
- eval_harness.py
- test_verification.py
- execute_with_retry
- scrub_pii
- test_security.py
- pytest
- IngestionQueue
- PersonaManagementModal
- llm.py
- graph.py
- api/auth.py
- test_interview_ws.py
- react
- errors.py
- LangGraph Orchestrator
- LocationNormalizer
- retrieve_stage1_candidates
- sqlalchemy_ext_asyncio
- jobs.py
- Dashboard.jsx
- create_or_update_application
- get_current_user
- fetch_company_intel
- OnboardingWizard
- UserAccount
- get_db
- asyncio
- test_agent_grounding.py
- calculate_match_upgraded
- devDependencies
- test_ats_llm.py
- test_candidates.py
- reset_test_llm
- App.jsx
- setup_tracing
- OmnisearchParser
- MetricsRegistry
- ._execute_task
- InterviewSimulator.jsx
- fastapi_testclient
- PIIScrubbingSpanProcessor
- .assemble_cors_lists
- .dispatch
- .with_structured_output
- matching.py
- JobListing
- PrometheusMetricsMiddleware
- InMemoryRateLimiter
- RateLimitMiddleware
- get_session_context
- api.js
- JobDiagnosticModal.jsx
- skill_graph.py
- Any
- test_migrations.py
- _scrub_attribute_value
- backup_db.sh
- agents/__init__.py
- nodes/__init__.py
- api/__init__.py
- core/__init__.py
- adapters/__init__.py
- ingestion/__init__.py
- ports/__init__.py
- app/__init__.py
- services/__init__.py
- tests/__init__.py
- career-os-backend
- DiscoveredJobDTO
- get_job_matches
- metrics_endpoint
- Database Architecture & Pure SQL Migrations Guide
- Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite
- TestHermeticIsolationAndConfig
- tracing.py
- test_security_headers.py
- calculate_semantic_top3_score
- db_session
- dependencies
- test_health_check_endpoint
- generate_golden_benchmark.py
- scripts
- build_run_config
- PersistentBudgetLedger
- CVBlock
- test_graph_recursion.py
- vite.config.js
- job_listing
- test_observability.py
- core/security.py
- patch_db
- test_probe_company_boards_discovers_valid_slug
- retrieve_and_rank_jobs
- AsyncSession
- datetime
- asyncio
- ParsedCVChunkSchema
- job_match_cache
- CurrentUser
- Depends
- tailor_node
- get
- UUID
- Base
- TimestampMixin
- UUIDMixin
- JobListing
- eval/__init__.py
- models/__init__.py
- JobListing
- BaseModel
- search.py
- pathlib
- calculate_freshness_score
- calculate_prestige_score
- calculate_probabilistic_gate
- calculate_seniority_score
- CompanyIntelExtractionSchema
- .assemble_and_validate_settings
- @testing-library/jest-dom
- UUID

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 64 edges
2. `JobListing` - 58 edges
3. `DiscoveredJobDTO` - 36 edges
4. `react` - 36 edges
5. `retrieve_and_rank_jobs()` - 31 edges
6. `CVBlock` - 28 edges
7. `CandidatePersona` - 28 edges
8. `calculate_match_upgraded()` - 23 edges
9. `Base` - 23 edges
10. `AshbyAdapter` - 23 edges

## Surprising Connections (you probably didn't know these)
- `crawl_selected_boards()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `print_statistics()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `seed_database_catalog()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `print_statistics()` --uses--> `JobListing`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/job_listing.py
- `crawl_board()` --uses--> `BoardSyncService`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/ingestion/service.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Agent Workflow** — master_spec_profiler_node, master_spec_hunter_node, master_spec_intel_node, master_spec_tailor_node, master_spec_ats_node, master_spec_coach_node, master_spec_reflector_node [EXTRACTED 1.00]
- **Frontend Presentation Architecture** — master_spec_dashboard_component, master_spec_ats_card_component, master_spec_interview_simulator_component [EXTRACTED 1.00]
- **Persistence and State Tiers** — master_spec_postgres_saver, master_spec_postgresql_database, master_spec_pgvector_extension [EXTRACTED 1.00]

## Communities (143 total, 34 thin omitted)

### Community 0 - "candidates.py"
Cohesion: 0.08
Nodes (58): commit_onboarding(), create_cv_block(), create_persona(), CreateSpecializedPersonaRequest, CVBlockCreateRequest, CVBlockResponse, delete_cv_block(), delete_persona() (+50 more)

### Community 1 - "models.py"
Cohesion: 0.08
Nodes (37): app_agents_llm, app_ingestion_ports_provider, classify_industry_vertical(), classify_visa_sponsorship(), extract_deterministic_requirements(), extract_domain_strictness(), extract_years_of_experience(), Deterministic requirements extraction and visa status classification. Pass 1 of… (+29 more)

### Community 2 - "typing"
Cohesion: 0.07
Nodes (50): Company intelligence gathering tool with Exa neural search and offline…, External tool integration wrappers for agent nodes. Each module wraps one…, Job search tool integration using JSearch API with hermetic offline fallbacks.…, Semantic vector search helper for CVBlock achievements using pgvector.…, CV generation and ATS evaluation loop API endpoints. This router exposes the…, User review and prompt weight reflection API endpoints. This router manages…, Bi-directional WebSocket endpoint for stateful mock interview coaching. This…, Authentication utilities with JWT signing and WebSocket thread protection. Why… (+42 more)

### Community 3 - "sqlalchemy"
Cohesion: 0.08
Nodes (41): Application tracker API endpoints. Enables candidates to save job listings and…, CircuitBreaker, Persistent rate-limit ledger and circuit breaker implementations. Guarantees…, Circuit breaker tracking consecutive failures and cooldown timers per provider., Check if provider is available or in active cooldown., Reset failure counts upon successful operation., Increment failure counter and trip breaker if threshold exceeded., Application (+33 more)

### Community 4 - "adapters/ats.py"
Cohesion: 0.07
Nodes (43): AshbyAdapter, _clean_html_to_text(), GreenhouseAdapter, LeverAdapter, AsyncClient, Tier-1 ATS client adapters for Greenhouse, Lever, Ashby, Workable, and…, Adapter for Lever Postings API. Docs: https://github.com/lever/postings-api…, Adapter for Ashby Job Postings API. Public endpoint:… (+35 more)

### Community 6 - "migrate.py"
Cohesion: 0.16
Nodes (23): Connection, apply_migrations(), baseline_migrations(), calculate_checksum(), ensure_tracking_table(), get_applied_migrations(), get_database_url(), get_migration_files() (+15 more)

### Community 7 - "diagnostics.py"
Cohesion: 0.14
Nodes (24): CompetencyDomainScore, DistinctionBadge, generate_holistic_audit(), generate_job_diagnostic(), generate_persona_market_benchmark(), HolisticCandidateAudit, JobDiagnosticReport, MarketSkillGapItem (+16 more)

### Community 8 - "test_matching.py"
Cohesion: 0.15
Nodes (17): app_agents_tools_embeddings, calculate_archetype_score(), calculate_compensation_score(), normalize_job_compensation(), Extract annualized USD base salary bounds (min_salary, max_salary,…, Calculate compensation feasibility S_comp with exponential shortfall penalty.…, Calculate job-specific archetype alignment S_archetype. Eliminates Job-…, Unit and integration tests for Two-Stage Matching Engine & Three-Tier… (+9 more)

### Community 9 - "BaseModel"
Cohesion: 0.12
Nodes (17): IngestJobUrlRequest, JobMatchesResponse, JobSearchRequest, JobSearchResponse, ParseQueryRequest, PasteJobTextRequest, BaseModel, Payload for natural language query tokenization. (+9 more)

### Community 10 - "embeddings.py"
Cohesion: 0.09
Nodes (32): app_core_database, app_models_cv_block, chunk_cv_text(), embed_text(), embed_texts(), _embedding_cache_key(), get_cached_embedding(), ingest_cv_blocks() (+24 more)

### Community 11 - "test_coach_llm.py"
Cohesion: 0.17
Nodes (12): coach_node(), Any, Process one conversational turn in the interactive mock interview. Reads: -…, FailingChatModel, asyncio, BaseChatModel, Unit tests for coach_node LLM generation and resilience., Simulated failing LLM to verify timeout and network resilience. (+4 more)

### Community 12 - "provider.py"
Cohesion: 0.14
Nodes (13): BudgetLedgerPort, CompanyContactProviderPort, ABC, Any, Port interfaces for ingestion providers, rate limiting, and repositories., Atomically check and increment quota permit. Returns True if allowed., Retrieve current usage and limits for a provider., Port for extracting structured ATS requirements from job descriptions. (+5 more)

### Community 13 - "test_cv_export.py"
Cohesion: 0.15
Nodes (15): format_cv_as_markdown(), format_cv_as_plaintext(), Any, CV export formatting utility producing clean, ATS-compliant text and Markdown.…, Format a tailored CV draft into a clean, single-column ATS Markdown document., Format a tailored CV draft into pure plain-text suitable for ATS paste-ins., Unit tests for CV export formatting and /api/cv/export endpoint., Verify markdown output contains title, summary, skills, and metrics. (+7 more)

### Community 14 - "api.py"
Cohesion: 0.10
Nodes (21): CompanyIntelPort, get_default_company_intel(), get_default_job_source(), JobListingDTO, JobSourcePort, LocalJobSourceService, ABC, Any (+13 more)

### Community 15 - "Evolution: Matching Engine v2.0 (Industrial-Grade Hybrid Retrieval)"
Cohesion: 0.10
Nodes (20): 1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 1. Two-Stage Retrieval Pipeline (Galene-Inspired), 2. Fault-Tolerant Parameter & Missing Data Handling, 2. Stage 2: Asymmetric Skill Graph & Specificity Weighting, 3. Real-World Signals: Prestige & Achievement Modeling, 3. Upgraded Multi-Factor Reranking Formula, 4. Compensation Normalization ($S_{\text{comp}}$) & Deduplication, 5. Explicit Domain Alignment ($S_{\text{domain}}$) & Context Blending ($S_{\text{context}}$) (+12 more)

### Community 16 - "package.json"
Cohesion: 0.14
Nodes (15): name, private, type, version, autoprefixer, axios, eslint, @eslint/js (+7 more)

### Community 17 - "Settings"
Cohesion: 0.14
Nodes (17): Return True if executing within automated pytest or test environment., Global application settings resolved from environment variables. Fields map…, Settings, Unit tests for Pydantic Settings configuration and validation., Verify workflow constants are properly defined in Settings., Verify DATABASE_URL is dynamically assembled from POSTGRES_* attributes., Verify caller-provided DATABASE_URL takes precedence over components., Verify production mode rejects localhost database connection strings. (+9 more)

### Community 18 - "company_intel_provider.py"
Cohesion: 0.07
Nodes (38): ProvenanceCompanyIntelService, Concrete implementation of CompanyIntelPort backed by Provenance provider., ProvenanceCompanyIntelProvider, AsyncSession, Provenance-tracked company intelligence provider. Replaces paid Exa / Apollo…, Synthesizes company dossiers with strict source grounding and provenance., Retrieve or refresh company intelligence with field-level provenance., GitHubOrgVerifier (+30 more)

### Community 19 - "AgentState"
Cohesion: 0.11
Nodes (33): Determine whether to route back to tailor_node or terminate the pipeline.…, route_ats(), AgentState, Execution state schema shared across all Career-OS LangGraph agent nodes. This…, _config(), asyncio, RunnableConfig, Unit and integration tests for LangGraph agent workflows and loop guards. (+25 more)

### Community 20 - "eval_harness.py"
Cohesion: 0.12
Nodes (22): aggregate_benchmark_metrics(), CandidateEvalMetrics, compute_dcg_at_k(), compute_gate_leakage(), compute_idcg_at_k(), compute_ndcg_at_k(), compute_precision_at_k(), compute_reciprocal_rank() (+14 more)

### Community 21 - "test_verification.py"
Cohesion: 0.09
Nodes (27): DefaultAggregatorCrossCheckAdapter, JobVerificationPort, JobVerificationService, Any, AsyncSession, UUID, Protocol for secondary aggregator cross-check providers., Query secondary aggregators for matching role. Returns None if not found, or a… (+19 more)

### Community 22 - "execute_with_retry"
Cohesion: 0.14
Nodes (13): execute_with_retry(), Any, Response, Execute an async HTTP call with bounded retries and exponential backoff. Args:…, asyncio, Verify that successful requests return immediately without additional retries., Verify recovery when initial attempts return transient 503 or 429 errors., Verify that network timeouts trigger retries up to max_retries limit. (+5 more)

### Community 23 - "scrub_pii"
Cohesion: 0.21
Nodes (8): Sanitize emails, phone numbers, and street addresses from prompt text.…, scrub_pii(), Test suite for regex sanitization of prompt inputs and outputs., Emails and phone numbers must be redacted., Street addresses must be replaced with redaction tokens., Technical skills, frameworks, and architecture terms must be untouched., Empty or falsy strings must return cleanly., TestPIIScrubbing

### Community 24 - "test_security.py"
Cohesion: 0.08
Nodes (32): Extract provider and slug from job apply URL and auto-register board. Promotes…, Probe official ATS endpoints for candidate slugs. Only queries official fixed…, Probe whether an ATS board slug exists and is active., Register a new ATS board in the database if not already present., parse_ats_url(), Exception, Security sterilization and validation for direct URLs and pasted user input.…, Parse a known direct ATS job posting or board URL. Returns: tuple of (provider,… (+24 more)

### Community 25 - "pytest"
Cohesion: 0.09
Nodes (26): AsyncPostgresSaver, close_postgres_saver(), init_postgres_saver(), Initialize persistent AsyncPostgresSaver and attach it to graph applications.…, Close the underlying PostgreSQL connection pool on shutdown., asyncio, Integration tests for Career-OS REST endpoints., Verify POST /api/jobs/search returns enriched jobs with company dossiers. (+18 more)

### Community 26 - "IngestionQueue"
Cohesion: 0.13
Nodes (22): IngestionTaskStatus, IngestionTaskType, Supported asynchronous ingestion queue task types., Status lifecycle of an ingestion queue task., IngestionQueue, Any, AsyncSession, datetime (+14 more)

### Community 27 - "PersonaManagementModal"
Cohesion: 0.19
Nodes (14): PersonaManagementModal(), handleCreatePersona(), handleDelete(), handleSaveEdit(), handleSetDefault(), PersonaSwitcher(), handleSelect(), loadPersonas() (+6 more)

### Community 28 - "llm.py"
Cohesion: 0.12
Nodes (18): asyncio, LLM provider abstraction and hermetic model factory for Career-OS agents. Why…, ATSAnalysisSchema, BaseModel, Applicant Tracking System (ATS) agent node and keyword gap evaluation. In…, Structured ATS evaluation produced via LLM., Coach agent node managing stateful, interactive mock technical interviews. The…, BaseModel (+10 more)

### Community 29 - "graph.py"
Cohesion: 0.11
Nodes (22): create_interview_graph(), create_pipeline_graph(), create_reflector_graph(), LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing. This…, Build and compile the stateful mock technical interview coaching graph. Each…, Build and compile the feedback synthesis and prompt directive reflection graph.…, Build and compile the end-to-end CV discovery, intelligence, and ATS graph.…, intel_node() (+14 more)

### Community 30 - "api/auth.py"
Cohesion: 0.06
Nodes (54): AuthResponse, get_current_user_profile(), login_account(), LoginRequest, PersonaSummaryResponse, BaseModel, CurrentUser, DatabaseSession (+46 more)

### Community 31 - "test_interview_ws.py"
Cohesion: 0.17
Nodes (11): Integration tests for bi-directional WebSocket mock interview endpoint., Verify plain unformatted text frames are treated as candidate message content., Verify WebSocket initializes coaching grounded in target job and company., Verify WebSocket looks up job title and company when given job_id., Verify non-object JSON frames return Bad Request error without crashing., Verify WebSocket bi-directional coaching exchange and session resumption., test_interview_websocket_handles_malformed_frames(), test_interview_websocket_initializes_with_target_job() (+3 more)

### Community 32 - "react"
Cohesion: 0.19
Nodes (11): ATSCard(), CVPreview(), SessionHistoryModal(), CVTailorView(), generateCV(), mockAuditData, mockMatchJob, mockParsedResult (+3 more)

### Community 33 - "errors.py"
Cohesion: 0.08
Nodes (32): create_problem_response(), http_exception_handler(), Any, Exception, FastAPI, Request, RFC 7807 Problem Details global exception handling. Why RFC 7807? Standard HTTP…, Catch-all handler for unexpected internal exceptions (HTTP 500). Logs full… (+24 more)

### Community 34 - "LangGraph Orchestrator"
Cohesion: 0.11
Nodes (24): API-First Decoupled Architecture, ATSCard Component, ATS Cyclic Feedback Loop, ATS Node, Stateful Career Operating System, Coach Node, CompanyDossier Model, CVBlock Model (+16 more)

### Community 35 - "LocationNormalizer"
Cohesion: 0.15
Nodes (19): LocationNormalizer, NormalizedLocation, ParsedVisaPolicy, Deterministic skills, location, and visa sponsorship taxonomy normalizers. Maps…, Structured location output., Normalizes unstructured location strings into granular geographical fields., Structured visa policy output., Parses immigration and work authorization terms from job descriptions. (+11 more)

### Community 36 - "retrieve_stage1_candidates"
Cohesion: 0.20
Nodes (13): build_stage1_query(), diagnose_zero_results(), get_stage1_count(), AsyncSession, Construct Stage 1 SQL query enforcing strict null-safety (ADR-008 & Spec…, Execute count query for a given filter set., Isolate which specific constraint caused zero results and generate actionable…, Stage 1 Hybrid Inverted Index & Reciprocal Rank Fusion (RRF) Retrieval. Defeats… (+5 more)

### Community 37 - "sqlalchemy_ext_asyncio"
Cohesion: 0.12
Nodes (16): Resilient asynchronous HTTP client helpers with timeouts and exponential…, generate_candidate_slugs(), ATS Board Discovery & Probing Engine. Discovers and registers new company ATS…, Generate normalized candidate board slugs for probing. e.g. 'Stripe, Inc.' ->…, Google News RSS and company news fetcher with 7-day TTL. Extracts dated…, Pytest fixtures for Career-OS testing. Provides in-memory SQLite async database…, Integration tests for Phase 6 Job Ingestion and Search API endpoints. Verifies:…, Unit tests for BoardDiscoveryEngine (slug generation, probing, and snowballing). (+8 more)

### Community 38 - "jobs.py"
Cohesion: 0.10
Nodes (21): app_agents_tools_company_intel, app_agents_tools_job_search, app_core_auth, app_core_config, app_core_logging, app_core_tracing, app_ingestion_adapters_ats, app_ingestion_company_intel_provider (+13 more)

### Community 39 - "Dashboard.jsx"
Cohesion: 0.12
Nodes (21): ADR-0008, AddJobModal(), CompanyDossierCard(), JobProvenanceBadge(), EmptyStateRelaxer(), InstrumentBar(), TokenizedOmnibar(), TYPE_COLORS (+13 more)

### Community 40 - "create_or_update_application"
Cohesion: 0.15
Nodes (18): ApplicationCreateRequest, ApplicationResponse, ApplicationStatusUpdateRequest, create_or_update_application(), list_applications(), BaseModel, CurrentUser, get (+10 more)

### Community 41 - "get_current_user"
Cohesion: 0.17
Nodes (12): authenticate_websocket(), get_current_user(), BaseModel, Depends, Request, WebSocket, FastAPI dependency extracting and validating the authenticated UserContext.…, Authenticate incoming WebSocket connection and verify thread ownership.… (+4 more)

### Community 42 - "fetch_company_intel"
Cohesion: 0.06
Nodes (39): fetch_company_intel(), Any, Fetch architectural intelligence and background for a target employer. Tries…, Any, Search for matching job listings using JSearch API or local fixtures. Queries…, search_jobs(), Any, AsyncSession (+31 more)

### Community 43 - "OnboardingWizard"
Cohesion: 0.16
Nodes (11): OnboardingWizard(), applyParsedData(), handleFileUpload(), handleFinalSubmit(), handleTextPasteSubmit(), POPULAR_SKILLS, SENIORITY_LEVELS, VISA_STATUS_OPTIONS (+3 more)

### Community 44 - "UserAccount"
Cohesion: 0.20
Nodes (10): TimestampMixin, Central authentication identity and master candidate account. Attributes:…, UserAccount, AsyncSession, Integration test verifying /api/jobs/matches, Tier 0 Audit, and Tier 1…, Verify Stage 1 RRF retrieves older, high-match jobs even when newer low-…, test_job_matching_and_diagnostics_api_flow(), test_stage1_rrf_prevents_recency_starvation() (+2 more)

### Community 45 - "get_db"
Cohesion: 0.16
Nodes (13): get_db(), Yield an async database session for use as a FastAPI dependency. Usage in a…, asyncio, AsyncSession, Verify registration, login, and profile retrieval endpoints., test_auth_register_login_and_me_flow(), asyncio, AsyncSession (+5 more)

### Community 46 - "asyncio"
Cohesion: 0.15
Nodes (13): asyncio, Verify valid ATS job posting URL is ingested and returns 201 Created., Verify pasting job description text stores as data_origin='manual'., Verify company intel refresh enforces 1-hour cooldown., Verify search response attachments include provenance and status., Verify empty query and location returns 200 with zero results without 422., Verify arbitrary web hosts and private IPs are rejected on direct URL import., test_company_intel_refresh_and_cooldown() (+5 more)

### Community 47 - "test_agent_grounding.py"
Cohesion: 0.16
Nodes (16): hunter_node(), Any, Hunter agent node discovering, ranking, and selecting target job listings. The…, Execute job board search and semantic pgvector ranking against candidate…, asyncio, Tests for Deep Agent Integration, Hunter Semantic pgvector Ranking, and ATS…, Verify Hunter selects AI Systems (job-ai-001) for LangGraph/pgvector candidate., Verify tailor_node extracts grounded requirements from raw description. (+8 more)

### Community 48 - "calculate_match_upgraded"
Cohesion: 0.20
Nodes (14): calculate_achievement_score(), calculate_domain_score(), calculate_match_upgraded(), derive_candidate_domain_profile(), Extract achievement merit markers (hackathons, open-source, publications).…, Derive candidate's normalized domain distribution vector D_cand and tenure. For…, Compute candidate's Domain Match Score S_domain and strictness beta_domain.…, Pure evaluation function computing P(Match) with full factor breakdown:… (+6 more)

### Community 49 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, eslint, @eslint/js, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+7 more)

### Community 50 - "test_ats_llm.py"
Cohesion: 0.17
Nodes (12): ats_node(), Any, Score the current CV draft against job criteria and identify keyword gaps.…, FailingChatModel, asyncio, BaseChatModel, Unit tests for ATS node LLM structured evaluation and threshold routing., Simulated failing LLM to verify resilience on error. (+4 more)

### Community 51 - "test_candidates.py"
Cohesion: 0.08
Nodes (41): parse_document_upload(), Parse an uploaded resume file (PDF, DOCX) and return structured staged data., detect_is_linkedin_pdf(), extract_metrics(), extract_skills_from_text(), extract_text_from_docx(), extract_text_from_pdf(), parse_generic_resume_text() (+33 more)

### Community 52 - "reset_test_llm"
Cohesion: 0.07
Nodes (44): get_llm(), MockChatModel, BaseChatModel, Override the model instance returned by ``get_llm`` for testing. Args: model:…, Clear any active test LLM override, restoring default resolution., Resolve and return a configured BaseChatModel instance. Selection Priority: 1.…, Deterministic mock chat model supporting structured outputs and cyclic reuse.…, reset_test_llm() (+36 more)

### Community 53 - "App.jsx"
Cohesion: 0.22
Nodes (8): App(), frontend_src_index, CandidateAuditView(), loadAudit(), getCandidateAudit(), getCurrentUser(), logout(), react-router-dom

### Community 54 - "setup_tracing"
Cohesion: 0.25
Nodes (7): flush_tracing(), Initialize OpenTelemetry TracerProvider with Phoenix OTLP HTTP exporter and…, Flush pending spans and cleanly shut down the OpenTelemetry provider., setup_tracing(), main(), CLI entrypoint for running the worker., Tracing setup and flush must complete safely without network calls.

### Community 55 - "OmnisearchParser"
Cohesion: 0.22
Nodes (11): app_services_skill_graph, parse_search_query(), Parse free-form query into tokenized filter entities and residual text., Result of parsing free-form search input into recognized entities and residual…, TokenizedFilterExtractionDTO, OmnisearchParser, Tokenizer and entity extraction service for the Command-Facet Omnibar. Parses…, Sub-2ms natural language query tokenizer and entity extractor. Maps free-form… (+3 more)

### Community 56 - "MetricsRegistry"
Cohesion: 0.18
Nodes (6): MetricsRegistry, Thread-safe Prometheus metrics collector and exposition formatter., Record an incoming HTTP request completion., Record completion of an agent graph workflow execution., Record an ATS revision cycle exhausting maximum revision bounds., Serialize registered metrics to standard Prometheus exposition format.

### Community 57 - "._execute_task"
Cohesion: 0.16
Nodes (9): IngestionWorker, Any, Route task to appropriate handler., Autonomous ingestion runner executing tasks from the ingestion_task queue., Signal worker to stop gracefully., Main event loop for the worker daemon., Fetch and execute a single task from the database queue., CircuitBreaker (+1 more)

### Community 58 - "InterviewSimulator.jsx"
Cohesion: 0.31
Nodes (5): getStoredSessions(), InterviewSimulator(), saveStoredSessions(), submitFeedback(), InterviewWebSocket

### Community 59 - "fastapi_testclient"
Cohesion: 0.08
Nodes (23): Unit tests for Prometheus metrics registry and /metrics endpoint., Verify that /metrics exports valid Prometheus text format., Verify metrics_registry records requests and computes summaries., test_metrics_endpoint_exports_prometheus_format(), test_metrics_registry_records_durations(), Unit tests for REST request payload limits and WebSocket frame size caps., Verify POST /api/cv/ingest rejects resume text exceeding MAX_CV_RAW_TEXT_LENGTH., Verify POST /api/feedback rejects feedback text exceeding… (+15 more)

### Community 60 - "PIIScrubbingSpanProcessor"
Cohesion: 0.18
Nodes (10): PIIScrubbingSpanProcessor, OpenTelemetry SpanProcessor that intercepts span attributes before batch export…, MonkeyPatch, Test suite for OpenTelemetry PIIScrubbingSpanProcessor., SpanProcessor on_end must sanitize string attributes., When PHOENIX_ANONYMIZE_PII is False, attributes must not be modified., TestSpanProcessorSanitization, Context (+2 more)

### Community 61 - ".assemble_cors_lists"
Cohesion: 0.29
Nodes (5): Any, Treat blank/empty strings in .env as None for optional API keys., Normalise list settings from multiple env-variable formats. Docker Compose and…, Validate sampling rate is within [0.0, 1.0]., field_validator

### Community 62 - ".dispatch"
Cohesion: 0.25
Nodes (7): CorrelationIdMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, FastAPI middleware to extract or inject X-Correlation-ID and log HTTP timing.…, Process incoming request, track latency, and attach correlation header.

### Community 63 - ".with_structured_output"
Cohesion: 0.25
Nodes (5): Any, Return the next simulated response or repeat the terminal entry., Produce a runnable chain that validates simulated JSON into a Pydantic model.…, BaseMessage, Runnable

### Community 64 - "matching.py"
Cohesion: 0.10
Nodes (25): app_ingestion_deterministic_extractor, app_models_application, app_models_base, app_models_ingestion, app_models_job_listing, app_models_user_account, app_models_user_profile, app_schemas_search (+17 more)

### Community 65 - "JobListing"
Cohesion: 0.11
Nodes (27): generate_deterministic_embedding(), Generate a deterministic, unit-normalized vector for hermetic testing. Uses…, JobListing, Stores discovered job listings, raw job descriptions, and ATS criteria., benchmark_evaluation_results(), golden_benchmark_data(), preloaded_jobs(), Any (+19 more)

### Community 66 - "PrometheusMetricsMiddleware"
Cohesion: 0.29
Nodes (6): PrometheusMetricsMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, Middleware recording HTTP request counts and durations into MetricsRegistry.

### Community 67 - "InMemoryRateLimiter"
Cohesion: 0.29
Nodes (4): InMemoryRateLimiter, Thread-safe sliding-window rate limiter keyed by client identifier., Check if the key exceeded limit within window_sec. Returns: (is_limited,…, Reset all rate limit counters (useful in tests).

### Community 68 - "RateLimitMiddleware"
Cohesion: 0.29
Nodes (6): BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, RateLimitMiddleware, HTTP middleware enforcing client IP rate limits on Career-OS routes.

### Community 69 - "get_session_context"
Cohesion: 0.17
Nodes (17): argparse, get_session_context(), AsyncSession, Provide an async session for standalone use outside of request scope. Use this…, crawl_board(), crawl_selected_boards(), _crawl_with_sem(), main() (+9 more)

### Community 70 - "api.js"
Cohesion: 0.26
Nodes (5): AuthModal(), handleSubmit(), apiClient, login(), register()

### Community 71 - "JobDiagnosticModal.jsx"
Cohesion: 0.53
Nodes (4): JobDiagnosticModal(), loadDiagnostics(), getJobDiagnostics(), mockDiagnosticData

### Community 72 - "skill_graph.py"
Cohesion: 0.15
Nodes (19): _stream1_score(), _build_transitive_matrix(), compute_asymmetric_skill_score(), expand_implied_skills(), get_skill_idf_weight(), get_transfer_weight(), normalize_skill(), Asymmetric Skill Graph, Directional Transfer Matrix, and IDF Specificity… (+11 more)

### Community 74 - "test_migrations.py"
Cohesion: 0.13
Nodes (14): Unit tests for Career-OS pure SQL migration runner and baseline integrity., Verify 0003_domain_alignment_schema.sql contains required domain alignment…, Verify SHA-256 calculation matches file hash., Verify show_status displays cleanly with mock connection., Verify 0001_initial_schema.sql is discovered in migrations directory., Verify initial schema file contains required extensions, tables, and seeds., Verify 0002_matching_engine_v2_schema.sql contains required v2 columns., test_checksum_calculation() (+6 more)

### Community 75 - "_scrub_attribute_value"
Cohesion: 0.33
Nodes (5): Any, Sanitize span attribute dictionaries before serialization., Recursively scrub strings within span attribute values., _scrub_attribute_value(), ReadableSpan

### Community 90 - "DiscoveredJobDTO"
Cohesion: 0.06
Nodes (43): ATSAdapterPort, ATSBoard, cross_check_job(), _format_job_dict(), ingest_job_from_url(), IngestJobResponse, paste_job_text(), Any (+35 more)

### Community 91 - "get_job_matches"
Cohesion: 0.23
Nodes (12): get_job_diagnostics(), get_job_matches(), _get_user_uuid(), AsyncSession, Two-Stage Job Retrieval, Command-Facet Filtering, and Probabilistic Reranker., Tier 1: Detailed diagnostic drilldown for a single job opportunity., Depends, description (+4 more)

### Community 92 - "metrics_endpoint"
Cohesion: 0.33
Nodes (6): health_check(), metrics_endpoint(), get, Response, Export Prometheus text format application and connection pool metrics., Return service health and database connectivity status. Executes a lightweight…

### Community 93 - "Database Architecture & Pure SQL Migrations Guide"
Cohesion: 0.18
Nodes (10): 1. Directory Structure, 2. Why Pure SQL Instead of Alembic?, 3.1 `uuid-ossp`, 3.2 `vector` (`pgvector`), 3. Required PostgreSQL Extensions, 4. Entity-Relationship & Table Overview, 5.1 Common Commands, 5.2 Tracking Table & Tampering Protection (+2 more)

### Community 94 - "Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite"
Cohesion: 0.18
Nodes (10): 1.1 Flaws in Baseline Matching Architecture, 1. Executive Summary & Problem Analysis, 2. Gap Analysis: System Requirements Previously Missing, 3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 3.2 Stage 2: Unified Multi-Factor Reranking Equation, 3. Upgraded Matching Engine Specification, 4. Evaluation Toolkit & Verification Suite, 5. Implementation Roadmap & Status (+2 more)

### Community 95 - "TestHermeticIsolationAndConfig"
Cohesion: 0.33
Nodes (4): Test suite for offline CI isolation and tracing configuration., In test environment, PHOENIX_ENABLED must resolve to False., Sampling rate must be between 0.0 and 1.0., TestHermeticIsolationAndConfig

### Community 96 - "tracing.py"
Cohesion: 0.20
Nodes (9): OpenTelemetry and Arize Phoenix tracing subsystem for Career-OS. Provides: -…, hmac, openinference_instrumentation_langchain, opentelemetry, opentelemetry_context, opentelemetry_exporter_otlp_proto_http_trace_exporter, opentelemetry_sdk_trace, opentelemetry_sdk_trace_export (+1 more)

### Community 97 - "test_security_headers.py"
Cohesion: 0.20
Nodes (9): Unit tests for HTTP security headers and CORS policy enforcement., Verify security headers are preserved on 4xx/5xx error responses., Verify CORS preflight returns configured allowed origin, methods, and headers., Verify untrusted origins outside CORS_ORIGINS do not receive allow headers., Verify OWASP security headers are attached to standard HTTP responses., test_cors_disallows_untrusted_origin(), test_cors_preflight_allowed_origin(), test_security_headers_present_on_error_responses() (+1 more)

### Community 98 - "calculate_semantic_top3_score"
Cohesion: 0.22
Nodes (10): calculate_semantic_top3_score(), _cosine_similarity(), Any, Compute cosine similarity between two float vectors., Extract list[float] from vector column or generate deterministic embedding., Calculate Top-3 Block Max-Sim semantic score S_semantic. Eliminates the double-…, _resolve_vector(), _stream2_score() (+2 more)

### Community 99 - "db_session"
Cohesion: 0.50
Nodes (4): db_session(), AsyncSession, fixture, Provide an isolated in-memory SQLite database session for unit tests. Creates…

### Community 100 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, axios, lucide-react, react, react-dom, react-router-dom

### Community 101 - "test_health_check_endpoint"
Cohesion: 0.67
Nodes (3): asyncio, Verify GET /health returns HTTP 200 and expected status payload., test_health_check_endpoint()

### Community 102 - "generate_golden_benchmark.py"
Cohesion: 0.24
Nodes (11): compute_ground_truth(), generate_benchmark_dataset(), generate_jobs_corpus(), main(), Any, Deterministic Generator for the 25-Candidate x 500-Job Matching Golden…, Generate 500 realistic, high-entropy job listings., Determine objective ground truth relevance score (0, 1, 2, 3) for (candidate,… (+3 more)

### Community 103 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 104 - "build_run_config"
Cohesion: 0.05
Nodes (43): CVExportRequest, CVGenerateRequest, CVGenerateResponse, CVIngestRequest, CVIngestResponse, export_tailored_cv(), generate_tailored_cv(), ingest_cv_document() (+35 more)

### Community 105 - "PersistentBudgetLedger"
Cohesion: 0.19
Nodes (8): PersistentBudgetLedger, Any, AsyncSession, Get current usage stats for a provider., PostgreSQL-backed atomic rate limiter and quota tracker., Resolve configured limits from Settings., Derive period bucket key (YYYY-MM-DD for daily or YYYY-MM-DD-HH for hourly)., Atomically reserve request permits. Returns True if granted, False if exceeded.

### Community 106 - "CVBlock"
Cohesion: 0.29
Nodes (7): CVBlock, Base, TimestampMixin, UUIDMixin, Stores granular career achievement blocks with pgvector embeddings. Attributes:…, Verify CVBlock stores content, category, metrics, and vector embedding., test_cv_block_embedding_structure()

### Community 107 - "test_graph_recursion.py"
Cohesion: 0.25
Nodes (7): asyncio, Unit tests for LangGraph recursion bounds and execution limit guards., Verify GRAPH_RECURSION_LIMIT is configured and exceeds single pass length., Verify that setting a low recursion limit raises GraphRecursionError., test_pipeline_graph_enforces_recursion_limit(), test_settings_defines_graph_recursion_limit(), langgraph_errors

### Community 108 - "vite.config.js"
Cohesion: 0.33
Nodes (5): __dirname, ref_node_path, ref_node_url, vite, @vitejs/plugin-react

### Community 109 - "job_listing"
Cohesion: 0.24
Nodes (10): cv_block, idx_cv_block_industry_tags_gin, idx_job_listing_industry_vertical, idx_job_listing_cbsa_metro_code, idx_job_listing_citizenship_restricted, idx_job_listing_excluded_states_gin, idx_job_listing_is_everify, idx_job_listing_lat_lon (+2 more)

### Community 110 - "test_observability.py"
Cohesion: 0.15
Nodes (9): Tests for Arize Phoenix observability, OpenTelemetry tracing, and PII…, Test suite for agent runs and ATS loop exhaustion metrics., record_agent_run must track execution counts and average latencies., route_ats tripping revision bounds must increment exhaustion metric., Test suite for CORS X-Correlation-ID exposure., Settings must configure CORS_EXPOSE_HEADERS with X-Correlation-ID., TestCORSExposeHeaders, TestMetricsAndLoopGuards (+1 more)

### Community 111 - "core/security.py"
Cohesion: 0.17
Nodes (10): BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, HTTP Security headers middleware and hardening policies. Why HTTP Security…, Inject OWASP-recommended HTTP security headers into every outgoing response., Process the HTTP request and attach hardened security headers to the response., SecurityHeadersMiddleware (+2 more)

### Community 112 - "patch_db"
Cohesion: 0.40
Nodes (4): patch_db(), AsyncSession, fixture, MonkeyPatch

### Community 113 - "test_probe_company_boards_discovers_valid_slug"
Cohesion: 0.50
Nodes (4): asyncio, AsyncSession, test_probe_company_boards_discovers_valid_slug(), test_snowball_from_apply_url()

### Community 114 - "retrieve_and_rank_jobs"
Cohesion: 0.25
Nodes (7): JobMatchResult, MatchFactorBreakdown, BaseModel, Execute two-stage job retrieval, reranking, and persistent caching. Stage 1:…, Detailed score decomposition for matching transparency., Final scored job listing opportunity returned to candidate feed., retrieve_and_rank_jobs()

### Community 118 - "ParsedCVChunkSchema"
Cohesion: 0.40
Nodes (5): ParsedCVChunkSchema, ParsedCVDocumentSchema, BaseModel, Structured extraction of an individual CV achievement block., List of extracted career achievement blocks from resume text.

### Community 122 - "tailor_node"
Cohesion: 0.17
Nodes (12): Any, Retrieve CV blocks from pgvector and assemble tailored CV draft. Reads: -…, tailor_node(), FailingChatModel, asyncio, BaseChatModel, Unit tests for tailor_node LLM synthesis and fallback behavior., Simulated failing LLM to verify resilience on error/timeout. (+4 more)

### Community 130 - "models/__init__.py"
Cohesion: 0.06
Nodes (38): The ATS provider identity., Base, Declarative base class for all SQLAlchemy relational models., FeedbackLog, Stores user reviews and Reflector agent synthesized prompt weight adjustments.…, ATSProvider, IndustrySector, IngestionRun (+30 more)

### Community 133 - "search.py"
Cohesion: 0.13
Nodes (19): GeoCoordinateDTO, JobSearchFilterDTO, BaseModel, Search engine schemas, DTOs, and enumeration contracts. Defines the Command-…, Diagnostic recommendation when zero results occur under strict filters., Search ranking mode. CV_GROUNDED: Ranks via P(Match) using candidate CV…, Tri-tier work authorization gating contract. ALL: No visa/citizenship…, Physical office requirement modality. (+11 more)

### Community 134 - "pathlib"
Cohesion: 0.40
Nodes (4): Unit test asserting the integrity and schema validity of data/seed_boards.yaml.…, test_seed_catalog_integrity(), pathlib, yaml

### Community 135 - "calculate_freshness_score"
Cohesion: 0.50
Nodes (4): calculate_freshness_score(), Calculate application timing advantage based on listing activation recency.…, Verify decay scoring reflecting the 3.8x recruiter callback rate window., test_calculate_freshness_score()

### Community 136 - "calculate_prestige_score"
Cohesion: 0.50
Nodes (4): calculate_prestige_score(), Score candidate pedigree based on prior employers and academic institutions.…, Verify prestige classification across Tier 1, Tier 2, and unlisted orgs., test_calculate_prestige_score()

### Community 137 - "calculate_probabilistic_gate"
Cohesion: 0.50
Nodes (4): calculate_probabilistic_gate(), Compute Bayesian uncertainty gate G_prob and hard-pass eligibility. Rules: -…, Critical ADR-002 verification: Missing visa sponsorship MUST NOT result in 0.0…, test_calculate_probabilistic_gate_bayesian_uncertainty()

### Community 138 - "calculate_seniority_score"
Cohesion: 0.50
Nodes (4): calculate_seniority_score(), Calibrate seniority level alignment between candidate and role., Verify seniority calibration and required years alignment., test_calculate_seniority_score()

### Community 139 - "CompanyIntelExtractionSchema"
Cohesion: 0.67
Nodes (3): CompanyIntelExtractionSchema, BaseModel, Structured extraction of company architecture and engineering culture.

## Knowledge Gaps
- **84 isolated node(s):** `1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF)`, `2. Fault-Tolerant Parameter & Missing Data Handling`, `2. Stage 2: Asymmetric Skill Graph & Specificity Weighting`, `3. Upgraded Multi-Factor Reranking Formula`, `4. Compensation Normalization ($S_{\text{comp}}$) & Deduplication` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1048 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JobListing` connect `JobListing` to `matching.py`, `models.py`, `models/__init__.py`, `sqlalchemy`, `calculate_semantic_top3_score`, `get_session_context`, `jobs.py`, `diagnostics.py`, `create_or_update_application`, `test_matching.py`, `UserAccount`, `api.py`, `calculate_match_upgraded`, `test_verification.py`, `._execute_task`, `DiscoveredJobDTO`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `AgentState` connect `AgentState` to `typing`, `build_run_config`, `fetch_company_intel`, `test_coach_llm.py`, `test_observability.py`, `test_agent_grounding.py`, `test_ats_llm.py`, `reset_test_llm`, `pytest`, `tailor_node`, `llm.py`, `graph.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `fetch_company_intel()` connect `fetch_company_intel` to `typing`, `get_session_context`, `api.py`, `company_intel_provider.py`, `reset_test_llm`, `execute_with_retry`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AgentState` (e.g. with `create_interview_graph()` and `create_pipeline_graph()`) actually correct?**
  _`AgentState` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `JobListing` (e.g. with `create_or_update_application()` and `list_applications()`) actually correct?**
  _`JobListing` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `DiscoveredJobDTO` (e.g. with `AshbyAdapter` and `GreenhouseAdapter`) actually correct?**
  _`DiscoveredJobDTO` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF)`, `2. Fault-Tolerant Parameter & Missing Data Handling`, `2. Stage 2: Asymmetric Skill Graph & Specificity Weighting` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._