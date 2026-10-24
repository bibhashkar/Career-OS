# Graph Report - career-os  (2026-10-23)

## Corpus Check
- 197 files · ~198,676 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .conf 1)

## Summary
- 2091 nodes · 4645 edges · 135 communities (110 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 382 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a887ad50`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _get_user_uuid
- deterministic_extractor.py
- typing
- sqlalchemy
- adapters/ats.py
- ingest_job_from_url
- migrate.py
- diagnostics.py
- test_matching.py
- DiscoveredJobDTO
- test_embeddings.py
- candidates.py
- sqlalchemy_ext_asyncio
- test_cv_export.py
- api.py
- Evolution: Matching Engine v2.0 (Industrial-Grade Hybrid Retrieval)
- package.json
- Settings
- test_intel_provider.py
- AgentState
- eval_harness.py
- JobListing
- execute_with_retry
- PIIScrubbingSpanProcessor
- test_security.py
- graph.py
- IngestionQueue
- PersonaManagementModal
- state.py
- asyncio
- api/auth.py
- test_interview_ws.py
- react
- errors.py
- LangGraph Orchestrator
- LocationNormalizer
- sanitize_text
- test_discovery.py
- models.py
- Dashboard.jsx
- create_or_update_application
- decode_access_token
- test_api_endpoints.py
- OnboardingWizard
- CandidatePersona
- test_auth_register_login_and_me_flow
- asyncio
- test_honesty.py
- LocalJobSourceService
- devDependencies
- FailingChatModel
- test_candidates.py
- pytest
- App.jsx
- core/security.py
- derive_subject_id
- MetricsRegistry
- FailingChatModel
- InterviewSimulator.jsx
- fastapi_testclient
- jobs.py
- submit_feedback
- .dispatch
- .with_structured_output
- CVBlock
- matching.py
- PrometheusMetricsMiddleware
- InMemoryRateLimiter
- RateLimitMiddleware
- crawl_jobs.py
- api.js
- JobDiagnosticModal.jsx
- skill_graph.py
- Any
- test_migrations.py
- TestCORSExposeHeaders
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
- BoardSyncService
- get_db
- test_ats_adapters.py
- Database Architecture & Pure SQL Migrations Guide
- Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite
- metrics_endpoint
- tracing.py
- test_security_headers.py
- generate_deterministic_embedding
- conftest.py
- company_intel_provider.py
- test_health_check_endpoint
- generate_golden_benchmark.py
- embed_text
- BaseModel
- CompanyIntelExtractionSchema
- export_tailored_cv
- test_graph_recursion.py
- JobListing
- 0003_domain_alignment_schema.sql
- SmartRecruitersAdapter
- _resolve_vector
- dependencies
- scripts
- retrieve_and_rank_jobs
- vite.config.js
- datetime
- asyncio
- ParsedCVChunkSchema
- job_match_cache
- patch_db
- pathlib
- FailingChatModel
- calculate_probabilistic_gate
- calculate_seniority_score
- ATSAnalysisSchema
- ReflectorDirectiveSchema
- merge_list
- SampleExtractionSchema
- eval/__init__.py
- test_user_profile_cv_blocks_strict_restrict_cascade
- test_table_names_are_singular
- @testing-library/jest-dom
- AsyncSession
- BaseModel

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 64 edges
2. `JobListing` - 50 edges
3. `DiscoveredJobDTO` - 36 edges
4. `CVBlock` - 33 edges
5. `react` - 32 edges
6. `CandidatePersona` - 31 edges
7. `retrieve_and_rank_jobs()` - 25 edges
8. `DataOrigin` - 25 edges
9. `UserAccount` - 25 edges
10. `ingest_job_from_url()` - 25 edges

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

## Communities (135 total, 25 thin omitted)

### Community 0 - "_get_user_uuid"
Cohesion: 0.15
Nodes (26): create_persona(), delete_cv_block(), delete_persona(), get_candidate_audit(), get_persona_benchmark(), _get_user_uuid(), list_cv_blocks(), list_personas() (+18 more)

### Community 1 - "deterministic_extractor.py"
Cohesion: 0.11
Nodes (28): app_agents_llm, classify_visa_sponsorship(), extract_deterministic_requirements(), extract_domain_strictness(), extract_years_of_experience(), Deterministic requirements extraction and visa status classification. Pass 1 of…, Extract domain strictness tier (beta_domain in [0.0, 1.0]). - 1.0…, Classify visa sponsorship as YES, NO, or UNKNOWN based on text evidence.… (+20 more)

### Community 2 - "typing"
Cohesion: 0.05
Nodes (65): Company intelligence gathering tool with Exa neural search and offline…, Embedding generation and semantic CV block chunking pipeline. Why semantic CV…, Job search tool integration using JSearch API with hermetic offline fallbacks.…, CV generation and ATS evaluation loop API endpoints. This router exposes the…, User review and prompt weight reflection API endpoints. This router manages…, interview_websocket_endpoint(), websocket, Bi-directional WebSocket endpoint for stateful mock interview coaching. This… (+57 more)

### Community 3 - "sqlalchemy"
Cohesion: 0.08
Nodes (52): app_models_application, app_models_company_dossier, Application tracker API endpoints. Enables candidates to save job listings and…, Application, Application model storing candidate job application tracker statuses. Tracks…, Candidate application tracking record. Attributes: user_profile_id: Foreign key…, Base, datetime (+44 more)

### Community 4 - "adapters/ats.py"
Cohesion: 0.12
Nodes (22): AshbyAdapter, GreenhouseAdapter, LeverAdapter, Tier-1 ATS client adapters for Greenhouse, Lever, Ashby, Workable, and…, Adapter for Lever Postings API. Docs: https://github.com/lever/postings-api…, Adapter for Ashby Job Postings API. Public endpoint:…, Adapter for Greenhouse Job Board API. Docs:…, BoardDiscoveryEngine (+14 more)

### Community 5 - "ingest_job_from_url"
Cohesion: 0.13
Nodes (23): fetch_company_intel(), Any, Fetch architectural intelligence and background for a target employer. Tries…, cross_check_job(), _format_job_dict(), ingest_job_from_url(), paste_job_text(), Any (+15 more)

### Community 6 - "migrate.py"
Cohesion: 0.16
Nodes (23): Connection, apply_migrations(), baseline_migrations(), calculate_checksum(), ensure_tracking_table(), get_applied_migrations(), get_database_url(), get_migration_files() (+15 more)

### Community 7 - "diagnostics.py"
Cohesion: 0.15
Nodes (22): CompetencyDomainScore, DistinctionBadge, generate_holistic_audit(), generate_job_diagnostic(), generate_persona_market_benchmark(), HolisticCandidateAudit, JobDiagnosticReport, MarketSkillGapItem (+14 more)

### Community 8 - "test_matching.py"
Cohesion: 0.09
Nodes (34): app_core_auth, calculate_achievement_score(), calculate_archetype_score(), calculate_compensation_score(), calculate_freshness_score(), calculate_match_upgraded(), calculate_prestige_score(), calculate_semantic_top3_score() (+26 more)

### Community 9 - "DiscoveredJobDTO"
Cohesion: 0.13
Nodes (11): Adapter for Workable Job Board API. Public list endpoint: POST…, WorkableAdapter, DiscoveredJobDTO, DTO representing a job posting discovered from an ATS or source., ATSAdapterPort, Port for ATS board adapters (Greenhouse, Lever, Ashby, etc.). Implementations…, The ATS provider identity., Fetch all currently open job postings for a company board slug. (+3 more)

### Community 10 - "test_embeddings.py"
Cohesion: 0.13
Nodes (19): chunk_cv_text(), ingest_cv_blocks(), Any, AsyncSession, UUID, Parse unstructured resume text into modular career achievement blocks. Uses LLM…, Embed career achievement blocks and persist them to PostgreSQL via pgvector.…, asyncio (+11 more)

### Community 11 - "candidates.py"
Cohesion: 0.12
Nodes (25): commit_onboarding(), create_cv_block(), CreateSpecializedPersonaRequest, CVBlockCreateRequest, CVBlockResponse, _get_or_create_account(), OnboardingCommitRequest, parse_pasted_text() (+17 more)

### Community 12 - "sqlalchemy_ext_asyncio"
Cohesion: 0.08
Nodes (28): CircuitBreaker, PersistentBudgetLedger, Any, AsyncSession, Persistent rate-limit ledger and circuit breaker implementations. Guarantees…, Get current usage stats for a provider., Circuit breaker tracking consecutive failures and cooldown timers per provider., Check if provider is available or in active cooldown. (+20 more)

### Community 13 - "test_cv_export.py"
Cohesion: 0.16
Nodes (14): format_cv_as_markdown(), format_cv_as_plaintext(), Any, Format a tailored CV draft into a clean, single-column ATS Markdown document., Format a tailored CV draft into pure plain-text suitable for ATS paste-ins., Unit tests for CV export formatting and /api/cv/export endpoint., Verify markdown output contains title, summary, skills, and metrics., Verify plaintext output is unformatted single-column text. (+6 more)

### Community 14 - "api.py"
Cohesion: 0.12
Nodes (24): CompanyIntelPort, get_default_company_intel(), get_default_job_source(), JobSourcePort, ProvenanceCompanyIntelService, ABC, Public Ingestion Boundary API & Domain Ports. As specified in ARCHITECTURE…, Force-refresh employer intelligence within cooldown constraints. (+16 more)

### Community 15 - "Evolution: Matching Engine v2.0 (Industrial-Grade Hybrid Retrieval)"
Cohesion: 0.10
Nodes (20): 1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 1. Two-Stage Retrieval Pipeline (Galene-Inspired), 2. Fault-Tolerant Parameter & Missing Data Handling, 2. Stage 2: Asymmetric Skill Graph & Specificity Weighting, 3. Real-World Signals: Prestige & Achievement Modeling, 3. Upgraded Multi-Factor Reranking Formula, 4. Compensation Normalization ($S_{\text{comp}}$) & Deduplication, 5. Explicit Domain Alignment ($S_{\text{domain}}$) & Context Blending ($S_{\text{context}}$) (+12 more)

### Community 16 - "package.json"
Cohesion: 0.14
Nodes (15): name, private, type, version, autoprefixer, axios, eslint, @eslint/js (+7 more)

### Community 17 - "Settings"
Cohesion: 0.07
Nodes (28): Any, Treat blank/empty strings in .env as None for optional API keys., Normalise list settings from multiple env-variable formats. Docker Compose and…, Validate sampling rate is within [0.0, 1.0]., Return True if executing within automated pytest or test environment., Derive DATABASE_URL from POSTGRES_* and validate production constraints., Global application settings resolved from environment variables. Fields map…, Settings (+20 more)

### Community 18 - "test_intel_provider.py"
Cohesion: 0.09
Nodes (23): AsyncSession, GitHubOrgVerifier, Any, AsyncClient, Verified GitHub organization crawler and tech stack analyzer. Extracts top…, Finds and verifies official GitHub organizations matching employer domain., Strip http/https, www, and trailing slashes for comparison., Verify GitHub org homepage matches company domain and extract top languages.… (+15 more)

### Community 19 - "AgentState"
Cohesion: 0.06
Nodes (60): create_pipeline_graph(), Determine whether to route back to tailor_node or terminate the pipeline.…, Build and compile the end-to-end CV discovery, intelligence, and ATS graph.…, route_ats(), ats_node(), Any, Score the current CV draft against job criteria and identify keyword gaps.…, hunter_node() (+52 more)

### Community 20 - "eval_harness.py"
Cohesion: 0.13
Nodes (21): aggregate_benchmark_metrics(), CandidateEvalMetrics, compute_dcg_at_k(), compute_gate_leakage(), compute_idcg_at_k(), compute_ndcg_at_k(), compute_precision_at_k(), compute_reciprocal_rank() (+13 more)

### Community 21 - "JobListing"
Cohesion: 0.07
Nodes (37): DefaultAggregatorCrossCheckAdapter, JobVerificationPort, JobVerificationService, Any, AsyncSession, UUID, Job Verification and Cross-Check Service. Provides secondary-source…, Protocol for secondary aggregator cross-check providers. (+29 more)

### Community 22 - "execute_with_retry"
Cohesion: 0.14
Nodes (13): execute_with_retry(), Any, Response, Execute an async HTTP call with bounded retries and exponential backoff. Args:…, asyncio, Verify that successful requests return immediately without additional retries., Verify recovery when initial attempts return transient 503 or 429 errors., Verify that network timeouts trigger retries up to max_retries limit. (+5 more)

### Community 23 - "PIIScrubbingSpanProcessor"
Cohesion: 0.08
Nodes (23): PIIScrubbingSpanProcessor, Any, Sanitize span attribute dictionaries before serialization., Sanitize emails, phone numbers, and street addresses from prompt text.…, Recursively scrub strings within span attribute values., OpenTelemetry SpanProcessor that intercepts span attributes before batch export…, _scrub_attribute_value(), scrub_pii() (+15 more)

### Community 24 - "test_security.py"
Cohesion: 0.11
Nodes (28): parse_ats_url(), Exception, Security sterilization and validation for direct URLs and pasted user input.…, Parse a known direct ATS job posting or board URL. Returns: tuple of (provider,…, Validate that an external HTTP(S) URL is safe to fetch. Rules: - Scheme must be…, Raised when URL or text fails security validation., SecurityValidationError, validate_and_guard_url() (+20 more)

### Community 25 - "graph.py"
Cohesion: 0.07
Nodes (32): AsyncPostgresSaver, close_postgres_saver(), create_interview_graph(), create_reflector_graph(), init_postgres_saver(), LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing. This…, Build and compile the stateful mock technical interview coaching graph. Each…, Build and compile the feedback synthesis and prompt directive reflection graph.… (+24 more)

### Community 26 - "IngestionQueue"
Cohesion: 0.08
Nodes (27): IngestionTaskStatus, IngestionTaskType, Supported asynchronous ingestion queue task types., Status lifecycle of an ingestion queue task., IngestionQueue, Any, AsyncSession, datetime (+19 more)

### Community 27 - "PersonaManagementModal"
Cohesion: 0.22
Nodes (13): PersonaManagementModal(), handleCreatePersona(), handleDelete(), handleSaveEdit(), handleSetDefault(), PersonaSwitcher(), handleSelect(), loadPersonas() (+5 more)

### Community 28 - "state.py"
Cohesion: 0.15
Nodes (16): asyncio, get_llm(), BaseChatModel, Resolve and return a configured BaseChatModel instance. Selection Priority: 1.…, Applicant Tracking System (ATS) agent node and keyword gap evaluation. In…, coach_node(), Any, Coach agent node managing stateful, interactive mock technical interviews. The… (+8 more)

### Community 29 - "asyncio"
Cohesion: 0.22
Nodes (9): asyncio, Verify POST /api/jobs/search returns enriched jobs with company dossiers., Verify POST /api/cv/generate returns tailored CV draft and ATS score., Verify POST /api/feedback synthesizes prompt weight adjustments., Verify feedback submissions never overwrite or corrupt interview state., test_cv_generate_endpoint(), test_feedback_does_not_pollute_interview_thread_state(), test_feedback_endpoint() (+1 more)

### Community 30 - "api/auth.py"
Cohesion: 0.08
Nodes (40): AuthResponse, get_current_user_profile(), login_account(), LoginRequest, PersonaSummaryResponse, BaseModel, CurrentUser, DatabaseSession (+32 more)

### Community 31 - "test_interview_ws.py"
Cohesion: 0.17
Nodes (11): Integration tests for bi-directional WebSocket mock interview endpoint., Verify plain unformatted text frames are treated as candidate message content., Verify WebSocket initializes coaching grounded in target job and company., Verify WebSocket looks up job title and company when given job_id., Verify non-object JSON frames return Bad Request error without crashing., Verify WebSocket bi-directional coaching exchange and session resumption., test_interview_websocket_handles_malformed_frames(), test_interview_websocket_initializes_with_target_job() (+3 more)

### Community 32 - "react"
Cohesion: 0.19
Nodes (13): ATSCard(), CompanyDossierCard(), CVPreview(), SessionHistoryModal(), CVTailorView(), generateCV(), refreshCompanyIntel(), mockAuditData (+5 more)

### Community 33 - "errors.py"
Cohesion: 0.08
Nodes (32): create_problem_response(), http_exception_handler(), Any, Exception, FastAPI, Request, RFC 7807 Problem Details global exception handling. Why RFC 7807? Standard HTTP…, Catch-all handler for unexpected internal exceptions (HTTP 500). Logs full… (+24 more)

### Community 34 - "LangGraph Orchestrator"
Cohesion: 0.11
Nodes (24): API-First Decoupled Architecture, ATSCard Component, ATS Cyclic Feedback Loop, ATS Node, Stateful Career Operating System, Coach Node, CompanyDossier Model, CVBlock Model (+16 more)

### Community 35 - "LocationNormalizer"
Cohesion: 0.15
Nodes (19): LocationNormalizer, NormalizedLocation, ParsedVisaPolicy, Deterministic skills, location, and visa sponsorship taxonomy normalizers. Maps…, Structured location output., Normalizes unstructured location strings into granular geographical fields., Structured visa policy output., Parses immigration and work authorization terms from job descriptions. (+11 more)

### Community 36 - "sanitize_text"
Cohesion: 0.33
Nodes (10): _clean_html_to_text(), Safely decode HTML entities and strip HTML markup into clean text., _fetch_detail(), _fetch_detail(), Physical work modality., Geographic & legal jurisdiction for remote roles., RemoteScope, WorkplaceType (+2 more)

### Community 37 - "test_discovery.py"
Cohesion: 0.13
Nodes (12): generate_candidate_slugs(), Extract provider and slug from job apply URL and auto-register board. Promotes…, Probe official ATS endpoints for candidate slugs. Only queries official fixed…, Probe whether an ATS board slug exists and is active., Generate normalized candidate board slugs for probing. e.g. 'Stripe, Inc.' ->…, Register a new ATS board in the database if not already present., asyncio, AsyncSession (+4 more)

### Community 38 - "models.py"
Cohesion: 0.08
Nodes (25): app_core_database, app_core_logging, app_core_tracing, app_ingestion_adapters_ats, app_ingestion_company_intel_provider, app_ingestion_discovery, app_ingestion_ledger, app_ingestion_ports_provider (+17 more)

### Community 39 - "Dashboard.jsx"
Cohesion: 0.18
Nodes (13): ADR-0008, AddJobModal(), JobProvenanceBadge(), Dashboard(), formatRelativeTime(), normalizeJobMatch(), SAMPLE_KEYWORDS, crossCheckJob() (+5 more)

### Community 40 - "create_or_update_application"
Cohesion: 0.15
Nodes (18): ApplicationCreateRequest, ApplicationResponse, ApplicationStatusUpdateRequest, create_or_update_application(), list_applications(), BaseModel, CurrentUser, get (+10 more)

### Community 41 - "decode_access_token"
Cohesion: 0.11
Nodes (19): _b64_decode(), decode_access_token(), get_current_user(), BaseModel, Depends, Request, Validate signature and expiration of an HS256 JWT, returning UserContext. Args:…, FastAPI dependency extracting and validating the authenticated UserContext.… (+11 more)

### Community 42 - "test_api_endpoints.py"
Cohesion: 0.09
Nodes (24): Hunter agent node discovering, ranking, and selecting target job listings. The…, External tool integration wrappers for agent nodes. Each module wraps one…, Any, Search for matching job listings using JSearch API or local fixtures. Queries…, search_jobs(), Any, AsyncSession, UUID (+16 more)

### Community 43 - "OnboardingWizard"
Cohesion: 0.15
Nodes (12): OnboardingWizard(), applyParsedData(), handleFileUpload(), handleFinalSubmit(), handleTextPasteSubmit(), POPULAR_SKILLS, SENIORITY_LEVELS, VISA_STATUS_OPTIONS (+4 more)

### Community 44 - "CandidatePersona"
Cohesion: 0.14
Nodes (20): CandidatePersona, JobMatchCache, PersonaSkill, Base, TimestampMixin, UUIDMixin, Target career persona representing a specialized professional lens. Every user…, Normalized technical and domain competency assigned to a candidate persona.… (+12 more)

### Community 45 - "test_auth_register_login_and_me_flow"
Cohesion: 0.40
Nodes (4): asyncio, AsyncSession, Verify registration, login, and profile retrieval endpoints., test_auth_register_login_and_me_flow()

### Community 46 - "asyncio"
Cohesion: 0.15
Nodes (13): asyncio, Verify valid ATS job posting URL is ingested and returns 201 Created., Verify pasting job description text stores as data_origin='manual'., Verify company intel refresh enforces 1-hour cooldown., Verify search response attachments include provenance and status., Verify empty query and location returns 200 with zero results without 422., Verify arbitrary web hosts and private IPs are rejected on direct URL import., test_company_intel_refresh_and_cooldown() (+5 more)

### Community 47 - "test_honesty.py"
Cohesion: 0.15
Nodes (14): asyncio, Unit tests validating Phase 0a honesty fixes. Verifies that: 1. Default…, Verify GEMINI_MODEL does not point to retired gemini-1.5-flash., Verify built-in mock jobs are explicitly labeled with data_origin='demo'., Verify built-in mock dossiers are explicitly labeled with data_origin='demo'., Verify search_jobs offline fallback preserves data_origin='demo'., Verify ats_node does not invent requirements when none specified., Verify unknown company intel does not invent fake publications. (+6 more)

### Community 48 - "LocalJobSourceService"
Cohesion: 0.19
Nodes (9): JobListingDTO, LocalJobSourceService, Any, Concrete implementation of JobSourcePort querying PostgreSQL JobListing…, Augmented DTO for fully parsed and registered job listings., Search local and synced job listings., Fetch a specific job listing by unique identifier., Verify LocalJobSourceService searches and gets jobs with hermetic fallbacks. (+1 more)

### Community 49 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, eslint, @eslint/js, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+7 more)

### Community 50 - "FailingChatModel"
Cohesion: 0.15
Nodes (7): FailingChatModel, BaseChatModel, Simulated failing LLM to verify resilience on error., FailingChatModel, BaseChatModel, FailingChatModel, BaseChatModel

### Community 51 - "test_candidates.py"
Cohesion: 0.07
Nodes (48): parse_document_upload(), Parse an uploaded resume file (PDF, DOCX) and return structured staged data., detect_is_linkedin_pdf(), extract_metrics(), extract_skills_from_text(), extract_text_from_docx(), extract_text_from_pdf(), parse_generic_resume_text() (+40 more)

### Community 52 - "pytest"
Cohesion: 0.07
Nodes (53): MockChatModel, LLM provider abstraction and hermetic model factory for Career-OS agents. Why…, Override the model instance returned by ``get_llm`` for testing. Args: model:…, Clear any active test LLM override, restoring default resolution., Deterministic mock chat model supporting structured outputs and cyclic reuse.…, reset_test_llm(), set_test_llm(), asyncio (+45 more)

### Community 53 - "App.jsx"
Cohesion: 0.27
Nodes (8): App(), frontend_src_index, CandidateAuditView(), loadAudit(), getCandidateAudit(), getCurrentUser(), logout(), react-router-dom

### Community 54 - "core/security.py"
Cohesion: 0.17
Nodes (10): BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, HTTP Security headers middleware and hardening policies. Why HTTP Security…, Inject OWASP-recommended HTTP security headers into every outgoing response., Process the HTTP request and attach hardened security headers to the response., SecurityHeadersMiddleware (+2 more)

### Community 55 - "derive_subject_id"
Cohesion: 0.21
Nodes (8): derive_subject_id(), Derive a deterministic, irreversible pseudonymous identifier for a candidate.…, Test suite for deterministic, PII-free subject ID hashing., The same candidate user ID must always yield the exact same subject_id., Subject ID must never leak the original user_id or email substring., Different candidate user IDs must produce distinct subject IDs., Empty or None user_id must cleanly map to 'subj_anonymous'., TestSubjectIdDerivation

### Community 56 - "MetricsRegistry"
Cohesion: 0.18
Nodes (6): MetricsRegistry, Thread-safe Prometheus metrics collector and exposition formatter., Record an incoming HTTP request completion., Record completion of an agent graph workflow execution., Record an ATS revision cycle exhausting maximum revision bounds., Serialize registered metrics to standard Prometheus exposition format.

### Community 57 - "FailingChatModel"
Cohesion: 0.40
Nodes (3): FailingChatModel, BaseChatModel, Simulated failing LLM to verify timeout and network resilience.

### Community 58 - "InterviewSimulator.jsx"
Cohesion: 0.31
Nodes (5): getStoredSessions(), InterviewSimulator(), saveStoredSessions(), submitFeedback(), InterviewWebSocket

### Community 59 - "fastapi_testclient"
Cohesion: 0.08
Nodes (23): Unit tests for Prometheus metrics registry and /metrics endpoint., Verify that /metrics exports valid Prometheus text format., Verify metrics_registry records requests and computes summaries., test_metrics_endpoint_exports_prometheus_format(), test_metrics_registry_records_durations(), Unit tests for REST request payload limits and WebSocket frame size caps., Verify POST /api/cv/ingest rejects resume text exceeding MAX_CV_RAW_TEXT_LENGTH., Verify POST /api/feedback rejects feedback text exceeding… (+15 more)

### Community 60 - "jobs.py"
Cohesion: 0.18
Nodes (15): IngestJobResponse, IngestJobUrlRequest, JobMatchesResponse, JobSearchRequest, JobSearchResponse, PasteJobTextRequest, BaseModel, Job search, manual ingestion, and company intelligence API endpoints. This… (+7 more)

### Community 61 - "submit_feedback"
Cohesion: 0.25
Nodes (9): FeedbackRequest, FeedbackResponse, BaseModel, CurrentUser, post, Payload for submitting user interview and coaching feedback. Attributes:…, Response confirming synthesized prompt weight adjustments. Attributes:…, Synthesize candidate feedback into updated agent prompt weights. Passes… (+1 more)

### Community 62 - ".dispatch"
Cohesion: 0.25
Nodes (7): CorrelationIdMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, FastAPI middleware to extract or inject X-Correlation-ID and log HTTP timing.…, Process incoming request, track latency, and attach correlation header.

### Community 63 - ".with_structured_output"
Cohesion: 0.25
Nodes (5): Any, Return the next simulated response or repeat the terminal entry., Produce a runnable chain that validates simulated JSON into a Pydantic model.…, BaseMessage, Runnable

### Community 64 - "CVBlock"
Cohesion: 0.15
Nodes (15): app_models_base, app_models_user_profile, CVBlock, Base, TimestampMixin, UUIDMixin, CVBlock model storing chunked user career achievements and embeddings. Career-…, Stores granular career achievement blocks with pgvector embeddings. Attributes:… (+7 more)

### Community 65 - "matching.py"
Cohesion: 0.14
Nodes (18): app_agents_tools_embeddings, app_ingestion_deterministic_extractor, app_models_cv_block, app_models_job_listing, app_models_user_account, app_services_skill_graph, Two-stage candidate-to-job retrieval, ranking, and probability scoring engine.…, IRBenchmarkSummary (+10 more)

### Community 66 - "PrometheusMetricsMiddleware"
Cohesion: 0.29
Nodes (6): PrometheusMetricsMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, Middleware recording HTTP request counts and durations into MetricsRegistry.

### Community 67 - "InMemoryRateLimiter"
Cohesion: 0.29
Nodes (4): InMemoryRateLimiter, Thread-safe sliding-window rate limiter keyed by client identifier., Check if the key exceeded limit within window_sec. Returns: (is_limited,…, Reset all rate limit counters (useful in tests).

### Community 68 - "RateLimitMiddleware"
Cohesion: 0.29
Nodes (6): BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, RateLimitMiddleware, HTTP middleware enforcing client IP rate limits on Career-OS routes.

### Community 69 - "crawl_jobs.py"
Cohesion: 0.19
Nodes (14): argparse, crawl_board(), crawl_selected_boards(), _crawl_with_sem(), main(), print_statistics(), Path, Print multi-dimensional repository metrics across sectors, geos, and modalities. (+6 more)

### Community 70 - "api.js"
Cohesion: 0.26
Nodes (5): AuthModal(), handleSubmit(), apiClient, login(), register()

### Community 71 - "JobDiagnosticModal.jsx"
Cohesion: 0.53
Nodes (4): JobDiagnosticModal(), loadDiagnostics(), getJobDiagnostics(), mockDiagnosticData

### Community 72 - "skill_graph.py"
Cohesion: 0.11
Nodes (24): calculate_skill_overlap(), Calculate normalized skill overlap and discover cross-technology matches. Args:…, _stream1_score(), _build_transitive_matrix(), compute_asymmetric_skill_score(), expand_implied_skills(), get_skill_idf_weight(), get_transfer_weight() (+16 more)

### Community 74 - "test_migrations.py"
Cohesion: 0.13
Nodes (14): Unit tests for Career-OS pure SQL migration runner and baseline integrity., Verify 0003_domain_alignment_schema.sql contains required domain alignment…, Verify SHA-256 calculation matches file hash., Verify show_status displays cleanly with mock connection., Verify 0001_initial_schema.sql is discovered in migrations directory., Verify initial schema file contains required extensions, tables, and seeds., Verify 0002_matching_engine_v2_schema.sql contains required v2 columns., test_checksum_calculation() (+6 more)

### Community 75 - "TestCORSExposeHeaders"
Cohesion: 0.50
Nodes (3): Test suite for CORS X-Correlation-ID exposure., Settings must configure CORS_EXPOSE_HEADERS with X-Correlation-ID., TestCORSExposeHeaders

### Community 90 - "BoardSyncService"
Cohesion: 0.19
Nodes (9): ATSAdapterPort, ATSBoard, BoardSyncService, Upsert a discovered job listing with foreign key relational integrity. Returns…, Synchronizes jobs from an ATS board into the local job_listing store., Register custom or mocked ATS adapter., Ensure an ATSBoard record exists in the database for relational safety., Execute full board sync: 1. Ensure ATSBoard entity exists in database. 2. Fetch… (+1 more)

### Community 91 - "get_db"
Cohesion: 0.23
Nodes (13): get_job_diagnostics(), get_job_matches(), _get_user_uuid(), AsyncSession, CurrentUser, Depends, get, UUID (+5 more)

### Community 92 - "test_ats_adapters.py"
Cohesion: 0.26
Nodes (8): asyncio, Unit tests for Tier-1 ATS adapters (Greenhouse, Lever, Ashby) with golden…, test_ashby_adapter_parses_golden_fixture(), test_greenhouse_adapter_parses_golden_fixture(), handler(), test_lever_adapter_parses_golden_fixture(), test_smartrecruiters_adapter_parses_golden_fixture(), test_workable_adapter_parses_golden_fixture()

### Community 93 - "Database Architecture & Pure SQL Migrations Guide"
Cohesion: 0.18
Nodes (10): 1. Directory Structure, 2. Why Pure SQL Instead of Alembic?, 3.1 `uuid-ossp`, 3.2 `vector` (`pgvector`), 3. Required PostgreSQL Extensions, 4. Entity-Relationship & Table Overview, 5.1 Common Commands, 5.2 Tracking Table & Tampering Protection (+2 more)

### Community 94 - "Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite"
Cohesion: 0.18
Nodes (10): 1.1 Flaws in Baseline Matching Architecture, 1. Executive Summary & Problem Analysis, 2. Gap Analysis: System Requirements Previously Missing, 3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 3.2 Stage 2: Unified Multi-Factor Reranking Equation, 3. Upgraded Matching Engine Specification, 4. Evaluation Toolkit & Verification Suite, 5. Implementation Roadmap & Status (+2 more)

### Community 95 - "metrics_endpoint"
Cohesion: 0.33
Nodes (6): health_check(), metrics_endpoint(), get, Response, Export Prometheus text format application and connection pool metrics., Return service health and database connectivity status. Executes a lightweight…

### Community 96 - "tracing.py"
Cohesion: 0.08
Nodes (24): flush_tracing(), OpenTelemetry and Arize Phoenix tracing subsystem for Career-OS. Provides: -…, Initialize OpenTelemetry TracerProvider with Phoenix OTLP HTTP exporter and…, Flush pending spans and cleanly shut down the OpenTelemetry provider., setup_tracing(), lifespan(), FastAPI, Manage application startup and teardown sequences. On startup: - Attempts to… (+16 more)

### Community 97 - "test_security_headers.py"
Cohesion: 0.20
Nodes (9): Unit tests for HTTP security headers and CORS policy enforcement., Verify security headers are preserved on 4xx/5xx error responses., Verify CORS preflight returns configured allowed origin, methods, and headers., Verify untrusted origins outside CORS_ORIGINS do not receive allow headers., Verify OWASP security headers are attached to standard HTTP responses., test_cors_disallows_untrusted_origin(), test_cors_preflight_allowed_origin(), test_security_headers_present_on_error_responses() (+1 more)

### Community 98 - "generate_deterministic_embedding"
Cohesion: 0.26
Nodes (12): generate_deterministic_embedding(), Generate a deterministic, unit-normalized vector for hermetic testing. Uses…, benchmark_evaluation_results(), golden_benchmark_data(), preloaded_jobs(), Any, JobListing, Production SLA: Stage 2 Reranker p95 latency < 45.0ms for 50 jobs. (+4 more)

### Community 99 - "conftest.py"
Cohesion: 0.29
Nodes (6): db_session(), AsyncSession, fixture, Pytest fixtures for Career-OS testing. Provides in-memory SQLite async database…, Provide an isolated in-memory SQLite database session for unit tests. Creates…, pytest_asyncio

### Community 100 - "company_intel_provider.py"
Cohesion: 0.12
Nodes (14): Provenance-tracked company intelligence provider. Replaces paid Exa / Apollo…, CompanyContactProviderPort, CompanyIntelProviderPort, ABC, Any, Port interfaces for ingestion providers, rate limiting, and repositories., Retrieve current usage and limits for a provider., Port for extracting structured ATS requirements from job descriptions. (+6 more)

### Community 101 - "test_health_check_endpoint"
Cohesion: 0.67
Nodes (3): asyncio, Verify GET /health returns HTTP 200 and expected status payload., test_health_check_endpoint()

### Community 102 - "generate_golden_benchmark.py"
Cohesion: 0.24
Nodes (11): compute_ground_truth(), generate_benchmark_dataset(), generate_jobs_corpus(), main(), Any, Deterministic Generator for the 25-Candidate x 500-Job Matching Golden…, Generate 500 realistic, high-entropy job listings., Determine objective ground truth relevance score (0, 1, 2, 3) for (candidate,… (+3 more)

### Community 103 - "embed_text"
Cohesion: 0.22
Nodes (11): embed_text(), embed_texts(), _embedding_cache_key(), get_cached_embedding(), _persist_with_session(), Generate deterministic SHA-256 hash digest for caching embedding vectors., Retrieve cached 1536-dim embedding vector if present., Store 1536-dim embedding vector in bounded LRU memory cache. (+3 more)

### Community 104 - "BaseModel"
Cohesion: 0.18
Nodes (11): CVExportRequest, CVGenerateRequest, CVGenerateResponse, CVIngestRequest, CVIngestResponse, BaseModel, Payload for uploading unstructured resume text or markdown., Response containing parsed career blocks and storage confirmation. (+3 more)

### Community 105 - "CompanyIntelExtractionSchema"
Cohesion: 0.67
Nodes (3): CompanyIntelExtractionSchema, BaseModel, Structured extraction of company architecture and engineering culture.

### Community 106 - "export_tailored_cv"
Cohesion: 0.28
Nodes (9): export_tailored_cv(), generate_tailored_cv(), ingest_cv_document(), CurrentUser, post, Response, Ingest unstructured resume text, decompose into semantic chunks, and embed.…, Export tailored CV draft as an ATS-clean Markdown or plaintext document.… (+1 more)

### Community 107 - "test_graph_recursion.py"
Cohesion: 0.25
Nodes (7): asyncio, Unit tests for LangGraph recursion bounds and execution limit guards., Verify GRAPH_RECURSION_LIMIT is configured and exceeds single pass length., Verify that setting a low recursion limit raises GraphRecursionError., test_pipeline_graph_enforces_recursion_limit(), test_settings_defines_graph_recursion_limit(), langgraph_errors

### Community 109 - "0003_domain_alignment_schema.sql"
Cohesion: 0.40
Nodes (4): cv_block, idx_cv_block_industry_tags_gin, idx_job_listing_industry_vertical, job_listing

### Community 110 - "SmartRecruitersAdapter"
Cohesion: 0.22
Nodes (3): AsyncClient, Adapter for SmartRecruiters Job Board API. Public list endpoint: GET…, SmartRecruitersAdapter

### Community 111 - "_resolve_vector"
Cohesion: 0.33
Nodes (6): _cosine_similarity(), Any, Compute cosine similarity between two float vectors., Extract list[float] from vector column or generate deterministic embedding., _resolve_vector(), _stream2_score()

### Community 112 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, axios, lucide-react, react, react-dom, react-router-dom

### Community 113 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 114 - "retrieve_and_rank_jobs"
Cohesion: 0.11
Nodes (22): AsyncSession, classify_industry_vertical(), Classify the primary vertical of a job posting based on employer and text…, calculate_domain_score(), derive_candidate_domain_profile(), JobMatchResult, MatchFactorBreakdown, Stage 1 Hybrid Inverted Index & Reciprocal Rank Fusion (RRF) Retrieval. Defeats… (+14 more)

### Community 115 - "vite.config.js"
Cohesion: 0.33
Nodes (5): __dirname, ref_node_path, ref_node_url, vite, @vitejs/plugin-react

### Community 118 - "ParsedCVChunkSchema"
Cohesion: 0.40
Nodes (5): ParsedCVChunkSchema, ParsedCVDocumentSchema, BaseModel, Structured extraction of an individual CV achievement block., List of extracted career achievement blocks from resume text.

### Community 120 - "patch_db"
Cohesion: 0.40
Nodes (4): patch_db(), AsyncSession, fixture, MonkeyPatch

### Community 121 - "pathlib"
Cohesion: 0.40
Nodes (4): Unit test asserting the integrity and schema validity of data/seed_boards.yaml.…, test_seed_catalog_integrity(), pathlib, yaml

### Community 122 - "FailingChatModel"
Cohesion: 0.40
Nodes (3): FailingChatModel, BaseChatModel, Simulated failing LLM to verify resilience on error/timeout.

### Community 123 - "calculate_probabilistic_gate"
Cohesion: 0.50
Nodes (4): calculate_probabilistic_gate(), Compute Bayesian uncertainty gate G_prob and hard-pass eligibility. Rules: -…, Critical ADR-002 verification: Missing visa sponsorship MUST NOT result in 0.0…, test_calculate_probabilistic_gate_bayesian_uncertainty()

### Community 124 - "calculate_seniority_score"
Cohesion: 0.50
Nodes (4): calculate_seniority_score(), Calibrate seniority level alignment between candidate and role., Verify seniority calibration and required years alignment., test_calculate_seniority_score()

### Community 125 - "ATSAnalysisSchema"
Cohesion: 0.67
Nodes (3): ATSAnalysisSchema, BaseModel, Structured ATS evaluation produced via LLM.

### Community 126 - "ReflectorDirectiveSchema"
Cohesion: 0.67
Nodes (3): BaseModel, Structured prompt weights extracted from qualitative user feedback., ReflectorDirectiveSchema

### Community 127 - "merge_list"
Cohesion: 0.67
Nodes (3): merge_list(), Any, Append incoming list items to the existing state list. Used as a LangGraph…

### Community 128 - "SampleExtractionSchema"
Cohesion: 0.67
Nodes (3): BaseModel, Pydantic model for structured output verification., SampleExtractionSchema

## Knowledge Gaps
- **82 isolated node(s):** `1.1 Flaws in Baseline Matching Architecture`, `2. Gap Analysis: System Requirements Previously Missing`, `3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF)`, `Context & Domain Alignment Blending ($S_{\text{context}}$)`, `4. Evaluation Toolkit & Verification Suite` (+77 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1001 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentState` connect `AgentState` to `tracing.py`, `typing`, `test_api_endpoints.py`, `export_tailored_cv`, `test_honesty.py`, `pytest`, `graph.py`, `state.py`, `submit_feedback`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `JobListing` connect `JobListing` to `CVBlock`, `sqlalchemy`, `IngestionQueue`, `ingest_job_from_url`, `models.py`, `adapters/ats.py`, `create_or_update_application`, `diagnostics.py`, `test_matching.py`, `crawl_jobs.py`, `CandidatePersona`, `api.py`, `LocalJobSourceService`, `retrieve_and_rank_jobs`, `BoardSyncService`, `jobs.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `tracing.py`, `typing`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AgentState` (e.g. with `create_interview_graph()` and `create_pipeline_graph()`) actually correct?**
  _`AgentState` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `JobListing` (e.g. with `create_or_update_application()` and `list_applications()`) actually correct?**
  _`JobListing` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `DiscoveredJobDTO` (e.g. with `AshbyAdapter` and `GreenhouseAdapter`) actually correct?**
  _`DiscoveredJobDTO` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `1.1 Flaws in Baseline Matching Architecture`, `2. Gap Analysis: System Requirements Previously Missing`, `3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF)` to the rest of the system?**
  _82 weakly-connected nodes found - possible documentation gaps or missing edges._