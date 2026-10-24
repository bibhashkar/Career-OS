# Graph Report - career-os  (2026-10-23)

## Corpus Check
- 205 files · ~205,667 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .conf 1)

## Summary
- 2188 nodes · 4829 edges · 134 communities (100 shown, 34 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 443 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3406d233`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- commit_onboarding
- deterministic_extractor.py
- logging.py
- sqlalchemy
- AshbyAdapter
- post
- migrate.py
- diagnostics.py
- JobListing
- DiscoveredJobDTO
- test_embeddings.py
- candidates.py
- sqlalchemy_ext_asyncio
- test_cv_export.py
- api.py
- Evolution: Matching Engine v2.0 (Industrial-Grade Hybrid Retrieval)
- package.json
- Settings
- typing
- AgentState
- eval_harness.py
- test_verification.py
- adapters/ats.py
- scrub_pii
- test_security.py
- pytest
- IngestionQueue
- api.js
- state.py
- graph.py
- api/auth.py
- test_interview_ws.py
- react
- errors.py
- LangGraph Orchestrator
- LocationNormalizer
- sanitize_text
- BoardDiscoveryEngine
- jobs.py
- Dashboard.jsx
- UUID
- get_current_user
- company_intel.py
- OnboardingWizard
- CandidatePersona
- test_job_matching_and_diagnostics_api_flow
- test_api_endpoints.py
- test_agent_grounding.py
- DataOrigin
- devDependencies
- nodes/ats.py
- test_candidates.py
- llm.py
- App.jsx
- main.py
- test_logging.py
- MetricsRegistry
- ._execute_task
- InterviewSimulator.jsx
- fastapi_testclient
- PIIScrubbingSpanProcessor
- submit_feedback
- .dispatch
- .with_structured_output
- user_account.py
- matching.py
- PrometheusMetricsMiddleware
- InMemoryRateLimiter
- RateLimitMiddleware
- get_session_context
- AuthModal.jsx
- JobDiagnosticModal.jsx
- skill_graph.py
- Any
- test_migrations.py
- ATSProvider
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
- search_and_intel
- get_job_matches
- asyncio
- Database Architecture & Pure SQL Migrations Guide
- Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite
- service.py
- tracing.py
- test_security_headers.py
- generate_deterministic_embedding
- conftest.py
- test_payload_limits.py
- test_health.py
- generate_golden_benchmark.py
- embed_text
- export_tailored_cv
- .acquire_permit
- CVBlock
- test_graph_recursion.py
- JobListing
- job_listing
- TestMetricsAndLoopGuards
- .dispatch
- vector_search.py
- app_models_job_listing
- JobMatchResult
- AsyncSession
- datetime
- asyncio
- ParsedCVChunkSchema
- job_match_cache
- CurrentUser
- Depends
- tailor.py
- get
- UUID
- Base
- TimestampMixin
- UUIDMixin
- JobListing
- eval/__init__.py
- test_models.py
- JobListing
- BaseModel
- test_search_engine.py

## God Nodes (most connected - your core abstractions)
1. `JobListing` - 68 edges
2. `AgentState` - 64 edges
3. `DiscoveredJobDTO` - 36 edges
4. `react` - 36 edges
5. `retrieve_and_rank_jobs()` - 35 edges
6. `CVBlock` - 31 edges
7. `CandidatePersona` - 28 edges
8. `search_and_intel()` - 23 edges
9. `calculate_match_upgraded()` - 23 edges
10. `Base` - 23 edges

## Surprising Connections (you probably didn't know these)
- `print_statistics()` --uses--> `JobListing`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/job_listing.py
- `crawl_selected_boards()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `print_statistics()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `seed_database_catalog()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `crawl_board()` --uses--> `BoardSyncService`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/ingestion/service.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Agent Workflow** — master_spec_profiler_node, master_spec_hunter_node, master_spec_intel_node, master_spec_tailor_node, master_spec_ats_node, master_spec_coach_node, master_spec_reflector_node [EXTRACTED 1.00]
- **Frontend Presentation Architecture** — master_spec_dashboard_component, master_spec_ats_card_component, master_spec_interview_simulator_component [EXTRACTED 1.00]
- **Persistence and State Tiers** — master_spec_postgres_saver, master_spec_postgresql_database, master_spec_pgvector_extension [EXTRACTED 1.00]

## Communities (134 total, 34 thin omitted)

### Community 0 - "commit_onboarding"
Cohesion: 0.13
Nodes (29): commit_onboarding(), create_persona(), delete_cv_block(), delete_persona(), get_candidate_audit(), get_persona_benchmark(), _get_user_uuid(), list_cv_blocks() (+21 more)

### Community 1 - "deterministic_extractor.py"
Cohesion: 0.12
Nodes (26): app_agents_llm, classify_visa_sponsorship(), extract_deterministic_requirements(), extract_years_of_experience(), Deterministic requirements extraction and visa status classification. Pass 1 of…, Classify visa sponsorship as YES, NO, or UNKNOWN based on text evidence.…, Extract minimum required years of experience from description text., Deterministic Pass 1: Extracts skills, minimum experience, visa status,… (+18 more)

### Community 2 - "logging.py"
Cohesion: 0.12
Nodes (26): Embedding generation and semantic CV block chunking pipeline. Why semantic CV…, Job search tool integration using JSearch API with hermetic offline fallbacks.…, CV generation and ATS evaluation loop API endpoints. This router exposes the…, User review and prompt weight reflection API endpoints. This router manages…, Bi-directional WebSocket endpoint for stateful mock interview coaching. This…, Authentication utilities with JWT signing and WebSocket thread protection. Why…, Application configuration via Pydantic BaseSettings. All runtime configuration…, SQLAlchemy async engine, session factory, and pgvector extension bootstrap.… (+18 more)

### Community 3 - "sqlalchemy"
Cohesion: 0.13
Nodes (37): Application model storing candidate job application tracker statuses. Tracks…, Base, datetime, Base SQLAlchemy declarative model and common audit mixins. This module provides…, Return timezone-aware current UTC datetime., Declarative base class for all SQLAlchemy relational models., Reusable mixin providing created_at and updated_at audit timestamps. All…, Reusable mixin providing standard UUIDv4 primary keys. Prevents enumeration… (+29 more)

### Community 4 - "AshbyAdapter"
Cohesion: 0.10
Nodes (19): AshbyAdapter, GreenhouseAdapter, LeverAdapter, AsyncClient, Adapter for Lever Postings API. Docs: https://github.com/lever/postings-api…, Adapter for Ashby Job Postings API. Public endpoint:…, Adapter for Greenhouse Job Board API. Docs:…, Adapter for SmartRecruiters Job Board API. Public list endpoint: GET… (+11 more)

### Community 6 - "migrate.py"
Cohesion: 0.16
Nodes (23): Connection, apply_migrations(), baseline_migrations(), calculate_checksum(), ensure_tracking_table(), get_applied_migrations(), get_database_url(), get_migration_files() (+15 more)

### Community 7 - "diagnostics.py"
Cohesion: 0.12
Nodes (26): CompetencyDomainScore, DistinctionBadge, generate_holistic_audit(), generate_job_diagnostic(), generate_persona_market_benchmark(), HolisticCandidateAudit, JobDiagnosticReport, MarketSkillGapItem (+18 more)

### Community 8 - "JobListing"
Cohesion: 0.06
Nodes (63): classify_industry_vertical(), extract_domain_strictness(), Classify the primary vertical of a job posting based on employer and text…, Extract domain strictness tier (beta_domain in [0.0, 1.0]). - 1.0…, JobListing, Stores discovered job listings, raw job descriptions, and ATS criteria., calculate_achievement_score(), calculate_archetype_score() (+55 more)

### Community 9 - "DiscoveredJobDTO"
Cohesion: 0.15
Nodes (10): Adapter for Workable Job Board API. Public list endpoint: POST…, WorkableAdapter, DiscoveredJobDTO, DTO representing a job posting discovered from an ATS or source., ATSAdapterPort, Port for ATS board adapters (Greenhouse, Lever, Ashby, etc.). Implementations…, Fetch all currently open job postings for a company board slug., Fetch full details and description for a specific job posting. (+2 more)

### Community 10 - "test_embeddings.py"
Cohesion: 0.16
Nodes (15): chunk_cv_text(), ingest_cv_blocks(), Any, AsyncSession, UUID, Parse unstructured resume text into modular career achievement blocks. Uses LLM…, Embed career achievement blocks and persist them to PostgreSQL via pgvector.…, asyncio (+7 more)

### Community 11 - "candidates.py"
Cohesion: 0.13
Nodes (22): create_cv_block(), CreateSpecializedPersonaRequest, CVBlockCreateRequest, CVBlockResponse, _get_or_create_account(), OnboardingCommitRequest, parse_pasted_text(), ParseTextRequest (+14 more)

### Community 12 - "sqlalchemy_ext_asyncio"
Cohesion: 0.07
Nodes (30): CircuitBreaker, PersistentBudgetLedger, AsyncSession, Persistent rate-limit ledger and circuit breaker implementations. Guarantees…, Circuit breaker tracking consecutive failures and cooldown timers per provider., Check if provider is available or in active cooldown., Reset failure counts upon successful operation., Increment failure counter and trip breaker if threshold exceeded. (+22 more)

### Community 13 - "test_cv_export.py"
Cohesion: 0.15
Nodes (15): format_cv_as_markdown(), format_cv_as_plaintext(), Any, CV export formatting utility producing clean, ATS-compliant text and Markdown.…, Format a tailored CV draft into a clean, single-column ATS Markdown document., Format a tailored CV draft into pure plain-text suitable for ATS paste-ins., Unit tests for CV export formatting and /api/cv/export endpoint., Verify markdown output contains title, summary, skills, and metrics. (+7 more)

### Community 14 - "api.py"
Cohesion: 0.09
Nodes (26): Intel agent node executing web research and company dossier synthesis. A…, CompanyIntelPort, get_default_company_intel(), get_default_job_source(), JobSourcePort, ProvenanceCompanyIntelService, ABC, Public Ingestion Boundary API & Domain Ports. As specified in ARCHITECTURE… (+18 more)

### Community 15 - "Evolution: Matching Engine v2.0 (Industrial-Grade Hybrid Retrieval)"
Cohesion: 0.10
Nodes (20): 1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 1. Two-Stage Retrieval Pipeline (Galene-Inspired), 2. Fault-Tolerant Parameter & Missing Data Handling, 2. Stage 2: Asymmetric Skill Graph & Specificity Weighting, 3. Real-World Signals: Prestige & Achievement Modeling, 3. Upgraded Multi-Factor Reranking Formula, 4. Compensation Normalization ($S_{\text{comp}}$) & Deduplication, 5. Explicit Domain Alignment ($S_{\text{domain}}$) & Context Blending ($S_{\text{context}}$) (+12 more)

### Community 16 - "package.json"
Cohesion: 0.06
Nodes (33): dependencies, axios, lucide-react, react, react-dom, react-router-dom, name, private (+25 more)

### Community 17 - "Settings"
Cohesion: 0.08
Nodes (25): Any, Treat blank/empty strings in .env as None for optional API keys., Normalise list settings from multiple env-variable formats. Docker Compose and…, Validate sampling rate is within [0.0, 1.0]., Return True if executing within automated pytest or test environment., Derive DATABASE_URL from POSTGRES_* and validate production constraints., Global application settings resolved from environment variables. Fields map…, Settings (+17 more)

### Community 18 - "typing"
Cohesion: 0.09
Nodes (24): Provenance-tracked company intelligence provider. Replaces paid Exa / Apollo…, GitHubOrgVerifier, Any, AsyncClient, Verified GitHub organization crawler and tech stack analyzer. Extracts top…, Finds and verifies official GitHub organizations matching employer domain., Strip http/https, www, and trailing slashes for comparison., Verify GitHub org homepage matches company domain and extract top languages.… (+16 more)

### Community 19 - "AgentState"
Cohesion: 0.11
Nodes (33): Determine whether to route back to tailor_node or terminate the pipeline.…, route_ats(), AgentState, Execution state schema shared across all Career-OS LangGraph agent nodes. This…, _config(), asyncio, RunnableConfig, Unit and integration tests for LangGraph agent workflows and loop guards. (+25 more)

### Community 20 - "eval_harness.py"
Cohesion: 0.12
Nodes (23): aggregate_benchmark_metrics(), CandidateEvalMetrics, compute_dcg_at_k(), compute_gate_leakage(), compute_idcg_at_k(), compute_ndcg_at_k(), compute_precision_at_k(), compute_reciprocal_rank() (+15 more)

### Community 21 - "test_verification.py"
Cohesion: 0.09
Nodes (27): DefaultAggregatorCrossCheckAdapter, JobVerificationPort, JobVerificationService, Any, AsyncSession, UUID, Protocol for secondary aggregator cross-check providers., Query secondary aggregators for matching role. Returns None if not found, or a… (+19 more)

### Community 22 - "adapters/ats.py"
Cohesion: 0.09
Nodes (23): execute_with_retry(), Any, Response, Resilient asynchronous HTTP client helpers with timeouts and exponential…, Execute an async HTTP call with bounded retries and exponential backoff. Args:…, Tier-1 ATS client adapters for Greenhouse, Lever, Ashby, Workable, and…, ATS Board Discovery & Probing Engine. Discovers and registers new company ATS…, Google News RSS and company news fetcher with 7-day TTL. Extracts dated… (+15 more)

### Community 23 - "scrub_pii"
Cohesion: 0.13
Nodes (13): Any, Sanitize span attribute dictionaries before serialization., Sanitize emails, phone numbers, and street addresses from prompt text.…, Recursively scrub strings within span attribute values., _scrub_attribute_value(), scrub_pii(), Test suite for regex sanitization of prompt inputs and outputs., Emails and phone numbers must be redacted. (+5 more)

### Community 24 - "test_security.py"
Cohesion: 0.11
Nodes (28): parse_ats_url(), Exception, Security sterilization and validation for direct URLs and pasted user input.…, Parse a known direct ATS job posting or board URL. Returns: tuple of (provider,…, Validate that an external HTTP(S) URL is safe to fetch. Rules: - Scheme must be…, Raised when URL or text fails security validation., SecurityValidationError, validate_and_guard_url() (+20 more)

### Community 25 - "pytest"
Cohesion: 0.10
Nodes (24): AsyncPostgresSaver, init_postgres_saver(), Initialize persistent AsyncPostgresSaver and attach it to graph applications.…, asyncio, Integration tests for Career-OS REST endpoints., Verify POST /api/jobs/search returns enriched jobs with company dossiers., Verify POST /api/cv/generate returns tailored CV draft and ATS score., Verify POST /api/feedback synthesizes prompt weight adjustments. (+16 more)

### Community 26 - "IngestionQueue"
Cohesion: 0.13
Nodes (20): IngestionTaskStatus, IngestionTaskType, Supported asynchronous ingestion queue task types., Status lifecycle of an ingestion queue task., IngestionQueue, Any, AsyncSession, datetime (+12 more)

### Community 27 - "api.js"
Cohesion: 0.15
Nodes (15): PersonaManagementModal(), handleCreatePersona(), handleDelete(), handleSaveEdit(), handleSetDefault(), PersonaSwitcher(), handleSelect(), loadPersonas() (+7 more)

### Community 28 - "state.py"
Cohesion: 0.11
Nodes (19): Any, BaseModel, Reflector agent node synthesizing candidate feedback into quantitative…, Structured prompt weights extracted from qualitative user feedback., Analyze candidate feedback and compute updated agent prompt weights. Reads: -…, reflector_node(), ReflectorDirectiveSchema, merge_list() (+11 more)

### Community 29 - "graph.py"
Cohesion: 0.11
Nodes (21): create_interview_graph(), create_pipeline_graph(), create_reflector_graph(), LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing. This…, Build and compile the stateful mock technical interview coaching graph. Each…, Build and compile the feedback synthesis and prompt directive reflection graph.…, Build and compile the end-to-end CV discovery, intelligence, and ATS graph.…, intel_node() (+13 more)

### Community 30 - "api/auth.py"
Cohesion: 0.06
Nodes (56): AuthResponse, get_current_user_profile(), login_account(), LoginRequest, PersonaSummaryResponse, BaseModel, CurrentUser, DatabaseSession (+48 more)

### Community 31 - "test_interview_ws.py"
Cohesion: 0.17
Nodes (11): Integration tests for bi-directional WebSocket mock interview endpoint., Verify plain unformatted text frames are treated as candidate message content., Verify WebSocket initializes coaching grounded in target job and company., Verify WebSocket looks up job title and company when given job_id., Verify non-object JSON frames return Bad Request error without crashing., Verify WebSocket bi-directional coaching exchange and session resumption., test_interview_websocket_handles_malformed_frames(), test_interview_websocket_initializes_with_target_job() (+3 more)

### Community 32 - "react"
Cohesion: 0.16
Nodes (13): ATSCard(), CompanyDossierCard(), CVPreview(), SessionHistoryModal(), CVTailorView(), generateCV(), refreshCompanyIntel(), mockAuditData (+5 more)

### Community 33 - "errors.py"
Cohesion: 0.13
Nodes (23): create_problem_response(), http_exception_handler(), Any, Exception, FastAPI, Request, RFC 7807 Problem Details global exception handling. Why RFC 7807? Standard HTTP…, Catch-all handler for unexpected internal exceptions (HTTP 500). Logs full… (+15 more)

### Community 34 - "LangGraph Orchestrator"
Cohesion: 0.11
Nodes (24): API-First Decoupled Architecture, ATSCard Component, ATS Cyclic Feedback Loop, ATS Node, Stateful Career Operating System, Coach Node, CompanyDossier Model, CVBlock Model (+16 more)

### Community 35 - "LocationNormalizer"
Cohesion: 0.15
Nodes (19): LocationNormalizer, NormalizedLocation, ParsedVisaPolicy, Deterministic skills, location, and visa sponsorship taxonomy normalizers. Maps…, Structured location output., Normalizes unstructured location strings into granular geographical fields., Structured visa policy output., Parses immigration and work authorization terms from job descriptions. (+11 more)

### Community 36 - "sanitize_text"
Cohesion: 0.26
Nodes (13): _clean_html_to_text(), Safely decode HTML entities and strip HTML markup into clean text., _fetch_detail(), _fetch_detail(), Physical work modality., Geographic & legal jurisdiction for remote roles., RemoteScope, WorkplaceType (+5 more)

### Community 37 - "BoardDiscoveryEngine"
Cohesion: 0.24
Nodes (10): BoardDiscoveryEngine, generate_candidate_slugs(), Generate normalized candidate board slugs for probing. e.g. 'Stripe, Inc.' ->…, Engine to discover, probe, and register ATS boards with entity protection., asyncio, AsyncSession, Unit tests for BoardDiscoveryEngine (slug generation, probing, and snowballing)., test_generate_candidate_slugs() (+2 more)

### Community 38 - "jobs.py"
Cohesion: 0.07
Nodes (37): app_agents_tools_company_intel, app_agents_tools_job_search, app_core_auth, app_core_config, app_core_database, app_core_logging, app_core_tracing, app_ingestion_adapters_ats (+29 more)

### Community 39 - "Dashboard.jsx"
Cohesion: 0.13
Nodes (19): ADR-0008, AddJobModal(), JobProvenanceBadge(), EmptyStateRelaxer(), InstrumentBar(), TokenizedOmnibar(), TYPE_COLORS, TYPE_ICONS (+11 more)

### Community 40 - "UUID"
Cohesion: 0.11
Nodes (27): ApplicationCreateRequest, ApplicationResponse, ApplicationStatusUpdateRequest, create_or_update_application(), list_applications(), BaseModel, CurrentUser, get (+19 more)

### Community 41 - "get_current_user"
Cohesion: 0.17
Nodes (12): authenticate_websocket(), get_current_user(), BaseModel, Depends, Request, WebSocket, FastAPI dependency extracting and validating the authenticated UserContext.…, Authenticate incoming WebSocket connection and verify thread ownership.… (+4 more)

### Community 42 - "company_intel.py"
Cohesion: 0.06
Nodes (40): CompanyIntelExtractionSchema, fetch_company_intel(), Any, BaseModel, Company intelligence gathering tool with Exa neural search and offline…, Fetch architectural intelligence and background for a target employer. Tries…, Structured extraction of company architecture and engineering culture., External tool integration wrappers for agent nodes. Each module wraps one… (+32 more)

### Community 43 - "OnboardingWizard"
Cohesion: 0.16
Nodes (11): OnboardingWizard(), applyParsedData(), handleFileUpload(), handleFinalSubmit(), handleTextPasteSubmit(), POPULAR_SKILLS, SENIORITY_LEVELS, VISA_STATUS_OPTIONS (+3 more)

### Community 44 - "CandidatePersona"
Cohesion: 0.18
Nodes (13): CandidatePersona, JobMatchCache, PersonaCVBlockRel, PersonaSkill, Base, TimestampMixin, UUIDMixin, Target career persona representing a specialized professional lens. Every user… (+5 more)

### Community 45 - "test_job_matching_and_diagnostics_api_flow"
Cohesion: 0.18
Nodes (9): get_db(), Yield an async database session for use as a FastAPI dependency. Usage in a…, asyncio, AsyncSession, Verify registration, login, and profile retrieval endpoints., test_auth_register_login_and_me_flow(), AsyncSession, Integration test verifying /api/jobs/matches, Tier 0 Audit, and Tier 1… (+1 more)

### Community 46 - "test_api_endpoints.py"
Cohesion: 0.13
Nodes (18): patch_db(), asyncio, AsyncSession, fixture, MonkeyPatch, Integration tests for Phase 6 Job Ingestion and Search API endpoints. Verifies:…, Verify valid ATS job posting URL is ingested and returns 201 Created., Verify pasting job description text stores as data_origin='manual'. (+10 more)

### Community 47 - "test_agent_grounding.py"
Cohesion: 0.15
Nodes (17): hunter_node(), Any, Hunter agent node discovering, ranking, and selecting target job listings. The…, Execute job board search and semantic pgvector ranking against candidate…, asyncio, Tests for Deep Agent Integration, Hunter Semantic pgvector Ranking, and ATS…, Verify Hunter selects AI Systems (job-ai-001) for LangGraph/pgvector candidate., Verify tailor_node extracts grounded requirements from raw description. (+9 more)

### Community 48 - "DataOrigin"
Cohesion: 0.21
Nodes (10): JobListingDTO, LocalJobSourceService, Any, Concrete implementation of JobSourcePort querying PostgreSQL JobListing…, Augmented DTO for fully parsed and registered job listings., Fetch a specific job listing by unique identifier., DataOrigin, Origin of a job listing or company dossier record. (+2 more)

### Community 49 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, eslint, @eslint/js, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+7 more)

### Community 50 - "nodes/ats.py"
Cohesion: 0.13
Nodes (16): ats_node(), ATSAnalysisSchema, Any, BaseModel, Applicant Tracking System (ATS) agent node and keyword gap evaluation. In…, Structured ATS evaluation produced via LLM., Score the current CV draft against job criteria and identify keyword gaps.…, FailingChatModel (+8 more)

### Community 51 - "test_candidates.py"
Cohesion: 0.07
Nodes (48): parse_document_upload(), Parse an uploaded resume file (PDF, DOCX) and return structured staged data., detect_is_linkedin_pdf(), extract_metrics(), extract_skills_from_text(), extract_text_from_docx(), extract_text_from_pdf(), parse_generic_resume_text() (+40 more)

### Community 52 - "llm.py"
Cohesion: 0.06
Nodes (49): get_llm(), MockChatModel, BaseChatModel, LLM provider abstraction and hermetic model factory for Career-OS agents. Why…, Override the model instance returned by ``get_llm`` for testing. Args: model:…, Clear any active test LLM override, restoring default resolution., Resolve and return a configured BaseChatModel instance. Selection Priority: 1.…, Deterministic mock chat model supporting structured outputs and cyclic reuse.… (+41 more)

### Community 53 - "App.jsx"
Cohesion: 0.22
Nodes (8): App(), frontend_src_index, CandidateAuditView(), loadAudit(), getCandidateAudit(), getCurrentUser(), logout(), react-router-dom

### Community 54 - "main.py"
Cohesion: 0.07
Nodes (32): close_postgres_saver(), Close the underlying PostgreSQL connection pool on shutdown., init_vector_extension(), Create the pgvector extension in PostgreSQL if it does not already exist.…, BaseHTTPMiddleware, HTTP Security headers middleware and hardening policies. Why HTTP Security…, Inject OWASP-recommended HTTP security headers into every outgoing response., SecurityHeadersMiddleware (+24 more)

### Community 55 - "test_logging.py"
Cohesion: 0.13
Nodes (17): Set the correlation ID for the current async task context., Format standard library log records as structured single-line JSON. Sanitizes…, Serialize log record attributes to JSON string., Configure application-wide root logger with StructuredJsonFormatter.…, set_correlation_id(), setup_logging(), StructuredJsonFormatter, Unit tests for structured JSON logging and correlation ID middleware. (+9 more)

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
Cohesion: 0.09
Nodes (19): Unit tests for RFC 7807 problem details error handling., Verify 404 responses conform to RFC 7807 application/problem+json., Verify schema validation failures format as RFC 7807 with invalid_params., test_404_not_found_returns_problem_details(), test_422_validation_error_returns_problem_details(), Unit tests for Prometheus metrics registry and /metrics endpoint., Verify that /metrics exports valid Prometheus text format., Verify metrics_registry records requests and computes summaries. (+11 more)

### Community 60 - "PIIScrubbingSpanProcessor"
Cohesion: 0.18
Nodes (10): PIIScrubbingSpanProcessor, OpenTelemetry SpanProcessor that intercepts span attributes before batch export…, MonkeyPatch, Test suite for OpenTelemetry PIIScrubbingSpanProcessor., SpanProcessor on_end must sanitize string attributes., When PHOENIX_ANONYMIZE_PII is False, attributes must not be modified., TestSpanProcessorSanitization, Context (+2 more)

### Community 61 - "submit_feedback"
Cohesion: 0.25
Nodes (9): FeedbackRequest, FeedbackResponse, BaseModel, CurrentUser, post, Payload for submitting user interview and coaching feedback. Attributes:…, Response confirming synthesized prompt weight adjustments. Attributes:…, Synthesize candidate feedback into updated agent prompt weights. Passes… (+1 more)

### Community 62 - ".dispatch"
Cohesion: 0.25
Nodes (7): CorrelationIdMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, FastAPI middleware to extract or inject X-Correlation-ID and log HTTP timing.…, Process incoming request, track latency, and attach correlation header.

### Community 63 - ".with_structured_output"
Cohesion: 0.25
Nodes (5): Any, Return the next simulated response or repeat the terminal entry., Produce a runnable chain that validates simulated JSON into a Pydantic model.…, BaseMessage, Runnable

### Community 64 - "user_account.py"
Cohesion: 0.36
Nodes (6): app_models_base, app_models_user_profile, CVBlock model storing chunked user career achievements and embeddings. Career-…, UserAccount, CandidatePersona, PersonaSkill, PersonaCVBlockRel, and…, pgvector_sqlalchemy, sqlalchemy_dialects_postgresql

### Community 65 - "matching.py"
Cohesion: 0.10
Nodes (25): app_agents_tools_embeddings, app_ingestion_deterministic_extractor, app_models_application, app_models_cv_block, app_models_ingestion, app_models_user_account, Job Verification and Cross-Check Service. Provides secondary-source…, JobListing model storing raw descriptions, requirements, and metadata. This… (+17 more)

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
Cohesion: 0.18
Nodes (16): argparse, get_session_context(), AsyncSession, Provide an async session for standalone use outside of request scope. Use this…, crawl_board(), crawl_selected_boards(), _crawl_with_sem(), main() (+8 more)

### Community 70 - "AuthModal.jsx"
Cohesion: 0.67
Nodes (4): AuthModal(), handleSubmit(), login(), register()

### Community 71 - "JobDiagnosticModal.jsx"
Cohesion: 0.53
Nodes (4): JobDiagnosticModal(), loadDiagnostics(), getJobDiagnostics(), mockDiagnosticData

### Community 72 - "skill_graph.py"
Cohesion: 0.15
Nodes (19): _stream1_score(), _build_transitive_matrix(), compute_asymmetric_skill_score(), expand_implied_skills(), get_skill_idf_weight(), get_transfer_weight(), normalize_skill(), Asymmetric Skill Graph, Directional Transfer Matrix, and IDF Specificity… (+11 more)

### Community 74 - "test_migrations.py"
Cohesion: 0.13
Nodes (14): Unit tests for Career-OS pure SQL migration runner and baseline integrity., Verify 0003_domain_alignment_schema.sql contains required domain alignment…, Verify SHA-256 calculation matches file hash., Verify show_status displays cleanly with mock connection., Verify 0001_initial_schema.sql is discovered in migrations directory., Verify initial schema file contains required extensions, tables, and seeds., Verify 0002_matching_engine_v2_schema.sql contains required v2 columns., test_checksum_calculation() (+6 more)

### Community 75 - "ATSProvider"
Cohesion: 0.20
Nodes (7): Extract provider and slug from job apply URL and auto-register board. Promotes…, Probe official ATS endpoints for candidate slugs. Only queries official fixed…, Probe whether an ATS board slug exists and is active., Register a new ATS board in the database if not already present., The ATS provider identity., ATSProvider, Reference lookup table for supported Applicant Tracking System providers.

### Community 90 - "search_and_intel"
Cohesion: 0.08
Nodes (37): ATSAdapterPort, ATSBoard, cross_check_job(), _format_job_dict(), ingest_job_from_url(), IngestJobResponse, parse_search_query(), paste_job_text() (+29 more)

### Community 91 - "get_job_matches"
Cohesion: 0.23
Nodes (12): get_job_diagnostics(), get_job_matches(), _get_user_uuid(), AsyncSession, Two-Stage Job Retrieval, Command-Facet Filtering, and Probabilistic Reranker., Tier 1: Detailed diagnostic drilldown for a single job opportunity., Depends, description (+4 more)

### Community 92 - "asyncio"
Cohesion: 0.25
Nodes (7): asyncio, test_ashby_adapter_parses_golden_fixture(), test_greenhouse_adapter_parses_golden_fixture(), handler(), test_lever_adapter_parses_golden_fixture(), test_smartrecruiters_adapter_parses_golden_fixture(), test_workable_adapter_parses_golden_fixture()

### Community 93 - "Database Architecture & Pure SQL Migrations Guide"
Cohesion: 0.18
Nodes (10): 1. Directory Structure, 2. Why Pure SQL Instead of Alembic?, 3.1 `uuid-ossp`, 3.2 `vector` (`pgvector`), 3. Required PostgreSQL Extensions, 4. Entity-Relationship & Table Overview, 5.1 Common Commands, 5.2 Tracking Table & Tampering Protection (+2 more)

### Community 94 - "Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite"
Cohesion: 0.18
Nodes (10): 1.1 Flaws in Baseline Matching Architecture, 1. Executive Summary & Problem Analysis, 2. Gap Analysis: System Requirements Previously Missing, 3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 3.2 Stage 2: Unified Multi-Factor Reranking Equation, 3. Upgraded Matching Engine Specification, 4. Evaluation Toolkit & Verification Suite, 5. Implementation Roadmap & Status (+2 more)

### Community 95 - "service.py"
Cohesion: 0.24
Nodes (9): app_ingestion_ports_provider, ListingStatus, Lifecycle status of a job listing., Board synchronization service and deduplication engine. Calculates cross-source…, asyncio, AsyncSession, Tests for BoardSyncService lifecycle, fingerprinting, and closed job detection., test_board_sync_lifecycle_and_closed_job_detection() (+1 more)

### Community 96 - "tracing.py"
Cohesion: 0.06
Nodes (32): interview_websocket_endpoint(), websocket, Stream interview dialogue bi-directionally keyed on thread_id checkpoint.…, get_correlation_id(), Retrieve the current task's correlation ID or empty string if unset., build_run_config(), derive_subject_id(), RunnableConfig (+24 more)

### Community 97 - "test_security_headers.py"
Cohesion: 0.20
Nodes (9): Unit tests for HTTP security headers and CORS policy enforcement., Verify security headers are preserved on 4xx/5xx error responses., Verify CORS preflight returns configured allowed origin, methods, and headers., Verify untrusted origins outside CORS_ORIGINS do not receive allow headers., Verify OWASP security headers are attached to standard HTTP responses., test_cors_disallows_untrusted_origin(), test_cors_preflight_allowed_origin(), test_security_headers_present_on_error_responses() (+1 more)

### Community 98 - "generate_deterministic_embedding"
Cohesion: 0.13
Nodes (19): generate_deterministic_embedding(), Generate a deterministic, unit-normalized vector for hermetic testing. Uses…, _cosine_similarity(), Any, Compute cosine similarity between two float vectors., Extract list[float] from vector column or generate deterministic embedding., _resolve_vector(), _stream2_score() (+11 more)

### Community 99 - "conftest.py"
Cohesion: 0.29
Nodes (6): db_session(), AsyncSession, fixture, Pytest fixtures for Career-OS testing. Provides in-memory SQLite async database…, Provide an isolated in-memory SQLite database session for unit tests. Creates…, pytest_asyncio

### Community 100 - "test_payload_limits.py"
Cohesion: 0.20
Nodes (9): Unit tests for REST request payload limits and WebSocket frame size caps., Verify POST /api/cv/ingest rejects resume text exceeding MAX_CV_RAW_TEXT_LENGTH., Verify POST /api/feedback rejects feedback text exceeding…, Verify POST /api/cv/generate rejects required_skills list with >50 items., Verify WebSocket endpoint returns Payload Too Large error frame on oversized…, test_cv_generate_rejects_excessive_skill_list(), test_cv_ingest_rejects_oversized_payload(), test_feedback_rejects_oversized_payload() (+1 more)

### Community 101 - "test_health.py"
Cohesion: 0.40
Nodes (4): asyncio, Integration tests for FastAPI health check endpoint., Verify GET /health returns HTTP 200 and expected status payload., test_health_check_endpoint()

### Community 102 - "generate_golden_benchmark.py"
Cohesion: 0.22
Nodes (12): compute_ground_truth(), generate_benchmark_dataset(), generate_jobs_corpus(), main(), Any, Deterministic Generator for the 25-Candidate x 500-Job Matching Golden…, Generate 500 realistic, high-entropy job listings., Determine objective ground truth relevance score (0, 1, 2, 3) for (candidate,… (+4 more)

### Community 103 - "embed_text"
Cohesion: 0.19
Nodes (13): embed_text(), embed_texts(), _embedding_cache_key(), get_cached_embedding(), _persist_with_session(), Generate deterministic SHA-256 hash digest for caching embedding vectors., Retrieve cached 1536-dim embedding vector if present., Store 1536-dim embedding vector in bounded LRU memory cache. (+5 more)

### Community 104 - "export_tailored_cv"
Cohesion: 0.13
Nodes (20): CVExportRequest, CVGenerateRequest, CVGenerateResponse, CVIngestRequest, CVIngestResponse, export_tailored_cv(), generate_tailored_cv(), ingest_cv_document() (+12 more)

### Community 105 - ".acquire_permit"
Cohesion: 0.25
Nodes (5): Any, Get current usage stats for a provider., Resolve configured limits from Settings., Derive period bucket key (YYYY-MM-DD for daily or YYYY-MM-DD-HH for hourly)., Atomically reserve request permits. Returns True if granted, False if exceeded.

### Community 106 - "CVBlock"
Cohesion: 0.29
Nodes (7): CVBlock, Base, TimestampMixin, UUIDMixin, Stores granular career achievement blocks with pgvector embeddings. Attributes:…, Verify CVBlock stores content, category, metrics, and vector embedding., test_cv_block_embedding_structure()

### Community 107 - "test_graph_recursion.py"
Cohesion: 0.25
Nodes (7): asyncio, Unit tests for LangGraph recursion bounds and execution limit guards., Verify GRAPH_RECURSION_LIMIT is configured and exceeds single pass length., Verify that setting a low recursion limit raises GraphRecursionError., test_pipeline_graph_enforces_recursion_limit(), test_settings_defines_graph_recursion_limit(), langgraph_errors

### Community 109 - "job_listing"
Cohesion: 0.24
Nodes (10): cv_block, idx_cv_block_industry_tags_gin, idx_job_listing_industry_vertical, idx_job_listing_cbsa_metro_code, idx_job_listing_citizenship_restricted, idx_job_listing_excluded_states_gin, idx_job_listing_is_everify, idx_job_listing_lat_lon (+2 more)

### Community 110 - "TestMetricsAndLoopGuards"
Cohesion: 0.33
Nodes (4): Test suite for agent runs and ATS loop exhaustion metrics., record_agent_run must track execution counts and average latencies., route_ats tripping revision bounds must increment exhaustion metric., TestMetricsAndLoopGuards

### Community 111 - ".dispatch"
Cohesion: 0.40
Nodes (4): Request, RequestResponseEndpoint, Response, Process the HTTP request and attach hardened security headers to the response.

### Community 114 - "JobMatchResult"
Cohesion: 0.40
Nodes (5): JobMatchResult, MatchFactorBreakdown, BaseModel, Detailed score decomposition for matching transparency., Final scored job listing opportunity returned to candidate feed.

### Community 118 - "ParsedCVChunkSchema"
Cohesion: 0.40
Nodes (5): ParsedCVChunkSchema, ParsedCVDocumentSchema, BaseModel, Structured extraction of an individual CV achievement block., List of extracted career achievement blocks from resume text.

### Community 122 - "tailor.py"
Cohesion: 0.15
Nodes (13): Any, Tailor agent node querying pgvector and assembling customized CV drafts. Rather…, Retrieve CV blocks from pgvector and assemble tailored CV draft. Reads: -…, tailor_node(), FailingChatModel, asyncio, BaseChatModel, Unit tests for tailor_node LLM synthesis and fallback behavior. (+5 more)

### Community 130 - "test_models.py"
Cohesion: 0.12
Nodes (15): Unit tests for SQLAlchemy models structure, relationships, and naming., Verify FeedbackLog stores thread_id, review feedback, and weights., Verify user_profile.cv_blocks enforces strict RESTRICT without delete-orphan., Verify Application model instantiation and default fields., Verify UserAccount, CandidatePersona, and PersonaSkill models., Verify all database table names strictly adhere to singular conventions., Verify UserProfile model can be instantiated with default fields., Verify JobListing foreign key to CompanyDossier. (+7 more)

### Community 133 - "test_search_engine.py"
Cohesion: 0.08
Nodes (42): app_schemas_search, app_services_skill_graph, asyncio, GeoCoordinateDTO, JobSearchFilterDTO, BaseModel, Search engine schemas, DTOs, and enumeration contracts. Defines the Command-…, Diagnostic recommendation when zero results occur under strict filters. (+34 more)

## Knowledge Gaps
- **84 isolated node(s):** `career-os-backend`, `TYPE_ICONS`, `TYPE_COLORS`, `SAMPLE_KEYWORDS`, `ADR-0008` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1048 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JobListing` connect `JobListing` to `user_account.py`, `matching.py`, `test_models.py`, `sqlalchemy`, `generate_deterministic_embedding`, `test_search_engine.py`, `jobs.py`, `diagnostics.py`, `UUID`, `get_session_context`, `test_job_matching_and_diagnostics_api_flow`, `api.py`, `DataOrigin`, `test_verification.py`, `._execute_task`, `search_and_intel`, `service.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `DiscoveredJobDTO` connect `DiscoveredJobDTO` to `AshbyAdapter`, `sanitize_text`, `sqlalchemy_ext_asyncio`, `api.py`, `test_api_endpoints.py`, `DataOrigin`, `typing`, `adapters/ats.py`, `search_and_intel`, `service.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `AgentState` connect `AgentState` to `tracing.py`, `logging.py`, `export_tailored_cv`, `company_intel.py`, `api.py`, `test_agent_grounding.py`, `TestMetricsAndLoopGuards`, `nodes/ats.py`, `submit_feedback`, `llm.py`, `pytest`, `tailor.py`, `state.py`, `graph.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `JobListing` (e.g. with `create_or_update_application()` and `list_applications()`) actually correct?**
  _`JobListing` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `AgentState` (e.g. with `create_interview_graph()` and `create_pipeline_graph()`) actually correct?**
  _`AgentState` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `DiscoveredJobDTO` (e.g. with `AshbyAdapter` and `GreenhouseAdapter`) actually correct?**
  _`DiscoveredJobDTO` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `career-os-backend`, `TYPE_ICONS`, `TYPE_COLORS` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._