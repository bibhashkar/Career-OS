# Graph Report - career-os  (2026-10-23)

## Corpus Check
- 192 files · ~119,015 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .conf 1)

## Summary
- 2029 nodes · 4544 edges · 121 communities (94 shown, 27 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 387 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5b1fbf43`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- candidates.py
- deterministic_extractor.py
- typing
- sqlalchemy
- adapters/ats.py
- test_reflector_llm.py
- migrate.py
- get_current_user
- JobListing
- models.py
- embeddings.py
- BaseModel
- PersistentBudgetLedger
- test_cv_export.py
- api.py
- ADR-008: High-Probability Job Matching, Two-Stage Retrieval & Fault-Tolerant Ranking
- package.json
- Settings
- company_intel_provider.py
- AgentState
- test_agent_grounding.py
- test_verification.py
- execute_with_retry
- PIIScrubbingSpanProcessor
- test_security.py
- graph.py
- IngestionQueue
- api.js
- llm.py
- pytest
- api/auth.py
- test_interview_ws.py
- react
- errors.py
- LangGraph Orchestrator
- LocationNormalizer
- sanitize_text
- test_discovery.py
- worker.py
- Dashboard.jsx
- create_or_update_application
- test_auth.py
- jobs.py
- OnboardingWizard
- CandidatePersona
- test_auth_register_login_and_me_flow
- test_api_endpoints.py
- test_honesty.py
- LocalJobSourceService
- devDependencies
- test_ats_llm.py
- test_candidates.py
- get_llm
- App.jsx
- core/security.py
- derive_subject_id
- MetricsRegistry
- test_coach_llm.py
- InterviewSimulator.jsx
- test_payload_limits.py
- HybridRequirementsExtractor
- submit_feedback
- .dispatch
- .with_structured_output
- job_listing.py
- app_models_cv_block
- PrometheusMetricsMiddleware
- InMemoryRateLimiter
- RateLimitMiddleware
- scrub_pii
- AuthModal.jsx
- JobDiagnosticModal.jsx
- skill_graph.py
- Any
- parse_document_upload
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
- lifespan
- get_db
- hash_password
- Database Architecture & Pure SQL Migrations Guide
- Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite
- metrics_endpoint
- tracing.py
- test_security_headers.py
- test_rate_limit.py
- collections_abc
- .get_usage
- test_health.py
- build_run_config
- fastapi_testclient
- _scrub_attribute_value
- CompanyIntelExtractionSchema
- commit_onboarding
- test_graph_recursion.py
- JobListing
- 0003_domain_alignment_schema.sql
- CompanyIntelProviderPort
- app_models_job_listing
- app_models_user_account
- app_services_skill_graph
- BaseModel
- CandidatePersona
- datetime
- asyncio
- CVBlock
- job_match_cache
- UserAccount

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 64 edges
2. `JobListing` - 58 edges
3. `CVBlock` - 42 edges
4. `CandidatePersona` - 37 edges
5. `DiscoveredJobDTO` - 36 edges
6. `react` - 32 edges
7. `UserAccount` - 29 edges
8. `retrieve_and_rank_jobs()` - 26 edges
9. `DataOrigin` - 25 edges
10. `ingest_job_from_url()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `crawl_board()` --uses--> `BoardSyncService`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/ingestion/service.py
- `print_statistics()` --uses--> `JobListing`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/job_listing.py
- `crawl_selected_boards()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `print_statistics()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `seed_database_catalog()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Agent Workflow** — master_spec_profiler_node, master_spec_hunter_node, master_spec_intel_node, master_spec_tailor_node, master_spec_ats_node, master_spec_coach_node, master_spec_reflector_node [EXTRACTED 1.00]
- **Frontend Presentation Architecture** — master_spec_dashboard_component, master_spec_ats_card_component, master_spec_interview_simulator_component [EXTRACTED 1.00]
- **Persistence and State Tiers** — master_spec_postgres_saver, master_spec_postgresql_database, master_spec_pgvector_extension [EXTRACTED 1.00]

## Communities (121 total, 27 thin omitted)

### Community 0 - "candidates.py"
Cohesion: 0.11
Nodes (38): create_cv_block(), create_persona(), delete_cv_block(), delete_persona(), get_candidate_audit(), _get_or_create_account(), get_persona_benchmark(), _get_user_uuid() (+30 more)

### Community 1 - "deterministic_extractor.py"
Cohesion: 0.19
Nodes (18): app_agents_llm, app_ingestion_ports_provider, classify_visa_sponsorship(), extract_deterministic_requirements(), extract_years_of_experience(), Deterministic requirements extraction and visa status classification. Pass 1 of…, Classify visa sponsorship as YES, NO, or UNKNOWN based on text evidence.…, Extract minimum required years of experience from description text. (+10 more)

### Community 2 - "typing"
Cohesion: 0.07
Nodes (48): Company intelligence gathering tool with Exa neural search and offline…, Job search tool integration using JSearch API with hermetic offline fallbacks.…, Application tracker API endpoints. Enables candidates to save job listings and…, CV generation and ATS evaluation loop API endpoints. This router exposes the…, User review and prompt weight reflection API endpoints. This router manages…, Bi-directional WebSocket endpoint for stateful mock interview coaching. This…, Authentication utilities with JWT signing and WebSocket thread protection. Why…, Application configuration via Pydantic BaseSettings. All runtime configuration… (+40 more)

### Community 3 - "sqlalchemy"
Cohesion: 0.07
Nodes (63): Persistent rate-limit ledger and circuit breaker implementations. Guarantees…, Application, Application model storing candidate job application tracker statuses. Tracks…, Candidate application tracking record. Attributes: user_profile_id: Foreign key…, Base, datetime, Base SQLAlchemy declarative model and common audit mixins. This module provides…, Return timezone-aware current UTC datetime. (+55 more)

### Community 4 - "adapters/ats.py"
Cohesion: 0.06
Nodes (43): ingest_job_from_url(), Ingest a job posting from a supported careers URL (Greenhouse, Lever, Ashby).…, Resilient asynchronous HTTP client helpers with timeouts and exponential…, AshbyAdapter, GreenhouseAdapter, LeverAdapter, AsyncClient, Tier-1 ATS client adapters for Greenhouse, Lever, Ashby, Workable, and… (+35 more)

### Community 5 - "test_reflector_llm.py"
Cohesion: 0.19
Nodes (11): Any, Analyze candidate feedback and compute updated agent prompt weights. Reads: -…, reflector_node(), FailingChatModel, asyncio, BaseChatModel, Unit tests for reflector_node structured LLM output and resilience., Verify reflector_node extracts prompt adjustments from structured LLM. (+3 more)

### Community 6 - "migrate.py"
Cohesion: 0.06
Nodes (51): argparse, Unit tests for Career-OS pure SQL migration runner and baseline integrity., Verify 0003_domain_alignment_schema.sql contains required domain alignment…, Verify SHA-256 calculation matches file hash., Verify show_status displays cleanly with mock connection., Verify 0001_initial_schema.sql is discovered in migrations directory., Verify initial schema file contains required extensions, tables, and seeds., Verify 0002_matching_engine_v2_schema.sql contains required v2 columns. (+43 more)

### Community 7 - "get_current_user"
Cohesion: 0.17
Nodes (12): authenticate_websocket(), get_current_user(), BaseModel, Depends, Request, WebSocket, FastAPI dependency extracting and validating the authenticated UserContext.…, Authenticate incoming WebSocket connection and verify thread ownership.… (+4 more)

### Community 8 - "JobListing"
Cohesion: 0.05
Nodes (83): app_agents_tools_embeddings, app_core_auth, _persist_with_session(), classify_industry_vertical(), extract_domain_strictness(), Classify the primary vertical of a job posting based on employer and text…, Extract domain strictness tier (beta_domain in [0.0, 1.0]). - 1.0…, CVBlock (+75 more)

### Community 9 - "models.py"
Cohesion: 0.05
Nodes (40): ATSAdapterPort, ATSBoard, DiscoveredJobDTO, ListingStatus, Pure domain data transfer objects (DTOs) and enums for data ingestion., DTO representing a job posting discovered from an ATS or source., Lifecycle status of a job listing., ATSAdapterPort (+32 more)

### Community 10 - "embeddings.py"
Cohesion: 0.08
Nodes (38): chunk_cv_text(), embed_text(), embed_texts(), _embedding_cache_key(), generate_deterministic_embedding(), get_cached_embedding(), ingest_cv_blocks(), ParsedCVChunkSchema (+30 more)

### Community 11 - "BaseModel"
Cohesion: 0.22
Nodes (9): CreateSpecializedPersonaRequest, CVBlockCreateRequest, CVBlockResponse, BaseModel, Payload for adding a new master CV achievement block., Response representing a persisted CVBlock entity., Payload for creating a specialized target career persona., Payload for updating or renaming a candidate persona. (+1 more)

### Community 12 - "PersistentBudgetLedger"
Cohesion: 0.10
Nodes (17): CircuitBreaker, PersistentBudgetLedger, Any, AsyncSession, Get current usage stats for a provider., Circuit breaker tracking consecutive failures and cooldown timers per provider., Check if provider is available or in active cooldown., Reset failure counts upon successful operation. (+9 more)

### Community 13 - "test_cv_export.py"
Cohesion: 0.07
Nodes (35): CVExportRequest, CVGenerateRequest, CVGenerateResponse, CVIngestRequest, CVIngestResponse, export_tailored_cv(), generate_tailored_cv(), ingest_cv_document() (+27 more)

### Community 14 - "api.py"
Cohesion: 0.13
Nodes (19): CompanyIntelPort, get_default_company_intel(), ProvenanceCompanyIntelService, ABC, Public Ingestion Boundary API & Domain Ports. As specified in ARCHITECTURE…, Force-refresh employer intelligence within cooldown constraints., Concrete implementation of CompanyIntelPort backed by Provenance provider., Return default application-wide CompanyIntelPort implementation. (+11 more)

### Community 15 - "ADR-008: High-Probability Job Matching, Two-Stage Retrieval & Fault-Tolerant Ranking"
Cohesion: 0.10
Nodes (19): 1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 1. Two-Stage Retrieval Pipeline (Galene-Inspired), 2. Fault-Tolerant Parameter & Missing Data Handling, 2. Stage 2: Asymmetric Skill Graph & Specificity Weighting, 3. Real-World Signals: Prestige & Achievement Modeling, 3. Upgraded Multi-Factor Reranking Formula, 4. Compensation Normalization ($S_{\text{comp}}$) & Deduplication, 5. Explicit Domain Alignment ($S_{\text{domain}}$) & Context Blending ($S_{\text{context}}$) (+11 more)

### Community 16 - "package.json"
Cohesion: 0.06
Nodes (33): dependencies, axios, lucide-react, react, react-dom, react-router-dom, name, private (+25 more)

### Community 17 - "Settings"
Cohesion: 0.07
Nodes (28): Any, Treat blank/empty strings in .env as None for optional API keys., Normalise list settings from multiple env-variable formats. Docker Compose and…, Validate sampling rate is within [0.0, 1.0]., Return True if executing within automated pytest or test environment., Derive DATABASE_URL from POSTGRES_* and validate production constraints., Global application settings resolved from environment variables. Fields map…, Settings (+20 more)

### Community 18 - "company_intel_provider.py"
Cohesion: 0.08
Nodes (28): Provenance-tracked company intelligence provider. Replaces paid Exa / Apollo…, GitHubOrgVerifier, Any, AsyncClient, Verified GitHub organization crawler and tech stack analyzer. Extracts top…, Finds and verifies official GitHub organizations matching employer domain., Strip http/https, www, and trailing slashes for comparison., Verify GitHub org homepage matches company domain and extract top languages.… (+20 more)

### Community 19 - "AgentState"
Cohesion: 0.10
Nodes (37): Determine whether to route back to tailor_node or terminate the pipeline.…, route_ats(), profiler_node(), Any, Profiler agent node establishing user constraints and stylistic directives. As…, Evaluate baseline user constraints and establish initial profile context.…, AgentState, Execution state schema shared across all Career-OS LangGraph agent nodes. This… (+29 more)

### Community 20 - "test_agent_grounding.py"
Cohesion: 0.13
Nodes (19): hunter_node(), Any, Hunter agent node discovering, ranking, and selecting target job listings. The…, Execute job board search and semantic pgvector ranking against candidate…, get_default_job_source(), Return default application-wide JobSourcePort implementation., asyncio, Tests for Deep Agent Integration, Hunter Semantic pgvector Ranking, and ATS… (+11 more)

### Community 21 - "test_verification.py"
Cohesion: 0.09
Nodes (27): DefaultAggregatorCrossCheckAdapter, JobVerificationPort, JobVerificationService, Any, AsyncSession, UUID, Protocol for secondary aggregator cross-check providers., Query secondary aggregators for matching role. Returns None if not found, or a… (+19 more)

### Community 22 - "execute_with_retry"
Cohesion: 0.14
Nodes (13): execute_with_retry(), Any, Response, Execute an async HTTP call with bounded retries and exponential backoff. Args:…, asyncio, Verify that successful requests return immediately without additional retries., Verify recovery when initial attempts return transient 503 or 429 errors., Verify that network timeouts trigger retries up to max_retries limit. (+5 more)

### Community 23 - "PIIScrubbingSpanProcessor"
Cohesion: 0.18
Nodes (10): PIIScrubbingSpanProcessor, OpenTelemetry SpanProcessor that intercepts span attributes before batch export…, MonkeyPatch, Test suite for OpenTelemetry PIIScrubbingSpanProcessor., SpanProcessor on_end must sanitize string attributes., When PHOENIX_ANONYMIZE_PII is False, attributes must not be modified., TestSpanProcessorSanitization, Context (+2 more)

### Community 24 - "test_security.py"
Cohesion: 0.15
Nodes (23): parse_ats_url(), Exception, Parse a known direct ATS job posting or board URL. Returns: tuple of (provider,…, Validate that an external HTTP(S) URL is safe to fetch. Rules: - Scheme must be…, Raised when URL or text fails security validation., SecurityValidationError, validate_and_guard_url(), MonkeyPatch (+15 more)

### Community 25 - "graph.py"
Cohesion: 0.08
Nodes (32): AsyncPostgresSaver, close_postgres_saver(), create_interview_graph(), create_pipeline_graph(), create_reflector_graph(), init_postgres_saver(), LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing. This…, Build and compile the stateful mock technical interview coaching graph. Each… (+24 more)

### Community 26 - "IngestionQueue"
Cohesion: 0.09
Nodes (25): IngestionTaskStatus, IngestionTaskType, Supported asynchronous ingestion queue task types., Status lifecycle of an ingestion queue task., IngestionQueue, Any, AsyncSession, datetime (+17 more)

### Community 27 - "api.js"
Cohesion: 0.15
Nodes (15): PersonaManagementModal(), handleCreatePersona(), handleDelete(), handleSaveEdit(), handleSetDefault(), PersonaSwitcher(), handleSelect(), loadPersonas() (+7 more)

### Community 28 - "llm.py"
Cohesion: 0.12
Nodes (18): asyncio, LLM provider abstraction and hermetic model factory for Career-OS agents. Why…, ATSAnalysisSchema, BaseModel, Applicant Tracking System (ATS) agent node and keyword gap evaluation. In…, Structured ATS evaluation produced via LLM., Coach agent node managing stateful, interactive mock technical interviews. The…, BaseModel (+10 more)

### Community 29 - "pytest"
Cohesion: 0.11
Nodes (17): asyncio, Integration tests for Career-OS REST endpoints., Verify POST /api/jobs/search returns enriched jobs with company dossiers., Verify POST /api/cv/generate returns tailored CV draft and ATS score., Verify POST /api/feedback synthesizes prompt weight adjustments., Verify feedback submissions never overwrite or corrupt interview state., test_cv_generate_endpoint(), test_feedback_does_not_pollute_interview_thread_state() (+9 more)

### Community 30 - "api/auth.py"
Cohesion: 0.14
Nodes (24): AuthResponse, get_current_user_profile(), login_account(), LoginRequest, PersonaSummaryResponse, BaseModel, CurrentUser, DatabaseSession (+16 more)

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
Cohesion: 0.22
Nodes (14): LocationNormalizer, Normalizes unstructured location strings into granular geographical fields., Parses immigration and work authorization terms from job descriptions., VisaSponsorshipParser, Tests for LocationNormalizer and VisaSponsorshipParser taxonomy engines., test_location_normalizer_australia(), test_location_normalizer_canada(), test_location_normalizer_city_state_us() (+6 more)

### Community 36 - "sanitize_text"
Cohesion: 0.23
Nodes (15): _clean_html_to_text(), Safely decode HTML entities and strip HTML markup into clean text., _fetch_detail(), _fetch_detail(), Physical work modality., Geographic & legal jurisdiction for remote roles., RemoteScope, WorkplaceType (+7 more)

### Community 37 - "test_discovery.py"
Cohesion: 0.10
Nodes (16): generate_candidate_slugs(), Extract provider and slug from job apply URL and auto-register board. Promotes…, Probe official ATS endpoints for candidate slugs. Only queries official fixed…, Probe whether an ATS board slug exists and is active., Generate normalized candidate board slugs for probing. e.g. 'Stripe, Inc.' ->…, Register a new ATS board in the database if not already present., asyncio, AsyncSession (+8 more)

### Community 38 - "worker.py"
Cohesion: 0.11
Nodes (18): app_core_database, app_core_logging, app_core_tracing, app_ingestion_adapters_ats, app_ingestion_company_intel_provider, app_ingestion_discovery, app_ingestion_ledger, app_ingestion_queue (+10 more)

### Community 39 - "Dashboard.jsx"
Cohesion: 0.18
Nodes (13): ADR-0008, AddJobModal(), JobProvenanceBadge(), Dashboard(), formatRelativeTime(), normalizeJobMatch(), SAMPLE_KEYWORDS, crossCheckJob() (+5 more)

### Community 40 - "create_or_update_application"
Cohesion: 0.15
Nodes (18): ApplicationCreateRequest, ApplicationResponse, ApplicationStatusUpdateRequest, create_or_update_application(), list_applications(), BaseModel, CurrentUser, get (+10 more)

### Community 41 - "test_auth.py"
Cohesion: 0.11
Nodes (24): _b64_decode(), _b64_encode(), create_access_token(), decode_access_token(), Create a signed HS256 JSON Web Token (JWT). Args: user_id: Candidate profile…, Validate signature and expiration of an HS256 JWT, returning UserContext. Args:…, Encode bytes into URL-safe base64 string without trailing padding., Decode URL-safe base64 string with restored padding. (+16 more)

### Community 42 - "jobs.py"
Cohesion: 0.05
Nodes (62): fetch_company_intel(), Any, Fetch architectural intelligence and background for a target employer. Tries…, External tool integration wrappers for agent nodes. Each module wraps one…, Any, Search for matching job listings using JSearch API or local fixtures. Queries…, search_jobs(), Any (+54 more)

### Community 43 - "OnboardingWizard"
Cohesion: 0.16
Nodes (11): OnboardingWizard(), applyParsedData(), handleFileUpload(), handleFinalSubmit(), handleTextPasteSubmit(), POPULAR_SKILLS, SENIORITY_LEVELS, VISA_STATUS_OPTIONS (+3 more)

### Community 44 - "CandidatePersona"
Cohesion: 0.08
Nodes (42): CandidatePersona, JobMatchCache, PersonaSkill, Base, TimestampMixin, UUIDMixin, Target career persona representing a specialized professional lens. Every user…, Normalized technical and domain competency assigned to a candidate persona.… (+34 more)

### Community 45 - "test_auth_register_login_and_me_flow"
Cohesion: 0.40
Nodes (4): asyncio, AsyncSession, Verify registration, login, and profile retrieval endpoints., test_auth_register_login_and_me_flow()

### Community 46 - "test_api_endpoints.py"
Cohesion: 0.13
Nodes (18): patch_db(), asyncio, AsyncSession, fixture, MonkeyPatch, Integration tests for Phase 6 Job Ingestion and Search API endpoints. Verifies:…, Verify valid ATS job posting URL is ingested and returns 201 Created., Verify pasting job description text stores as data_origin='manual'. (+10 more)

### Community 47 - "test_honesty.py"
Cohesion: 0.15
Nodes (14): asyncio, Unit tests validating Phase 0a honesty fixes. Verifies that: 1. Default…, Verify GEMINI_MODEL does not point to retired gemini-1.5-flash., Verify built-in mock jobs are explicitly labeled with data_origin='demo'., Verify built-in mock dossiers are explicitly labeled with data_origin='demo'., Verify search_jobs offline fallback preserves data_origin='demo'., Verify ats_node does not invent requirements when none specified., Verify unknown company intel does not invent fake publications. (+6 more)

### Community 48 - "LocalJobSourceService"
Cohesion: 0.18
Nodes (11): JobListingDTO, JobSourcePort, LocalJobSourceService, Any, Concrete implementation of JobSourcePort querying PostgreSQL JobListing…, Augmented DTO for fully parsed and registered job listings., Port for finding and querying job postings., Search local and synced job listings. (+3 more)

### Community 49 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, eslint, @eslint/js, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+7 more)

### Community 50 - "test_ats_llm.py"
Cohesion: 0.17
Nodes (12): ats_node(), Any, Score the current CV draft against job criteria and identify keyword gaps.…, FailingChatModel, asyncio, BaseChatModel, Unit tests for ATS node LLM structured evaluation and threshold routing., Simulated failing LLM to verify resilience on error. (+4 more)

### Community 51 - "test_candidates.py"
Cohesion: 0.09
Nodes (37): detect_is_linkedin_pdf(), extract_metrics(), extract_skills_from_text(), extract_text_from_docx(), extract_text_from_pdf(), parse_generic_resume_text(), parse_linkedin_text(), parse_resume_bytes() (+29 more)

### Community 52 - "get_llm"
Cohesion: 0.06
Nodes (45): get_llm(), MockChatModel, BaseChatModel, Override the model instance returned by ``get_llm`` for testing. Args: model:…, Clear any active test LLM override, restoring default resolution., Resolve and return a configured BaseChatModel instance. Selection Priority: 1.…, Deterministic mock chat model supporting structured outputs and cyclic reuse.…, reset_test_llm() (+37 more)

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

### Community 57 - "test_coach_llm.py"
Cohesion: 0.17
Nodes (12): coach_node(), Any, Process one conversational turn in the interactive mock interview. Reads: -…, FailingChatModel, asyncio, BaseChatModel, Unit tests for coach_node LLM generation and resilience., Simulated failing LLM to verify timeout and network resilience. (+4 more)

### Community 58 - "InterviewSimulator.jsx"
Cohesion: 0.31
Nodes (5): getStoredSessions(), InterviewSimulator(), saveStoredSessions(), submitFeedback(), InterviewWebSocket

### Community 59 - "test_payload_limits.py"
Cohesion: 0.20
Nodes (9): Unit tests for REST request payload limits and WebSocket frame size caps., Verify POST /api/cv/ingest rejects resume text exceeding MAX_CV_RAW_TEXT_LENGTH., Verify POST /api/feedback rejects feedback text exceeding…, Verify POST /api/cv/generate rejects required_skills list with >50 items., Verify WebSocket endpoint returns Payload Too Large error frame on oversized…, test_cv_generate_rejects_excessive_skill_list(), test_cv_ingest_rejects_oversized_payload(), test_feedback_rejects_oversized_payload() (+1 more)

### Community 60 - "HybridRequirementsExtractor"
Cohesion: 0.15
Nodes (10): HybridRequirementsExtractor, Any, Two-pass requirements extraction with grounding validation., Check if a candidate skill from the LLM is grounded in the source text., ParsedRequirementsDTO, DTO representing structured technical and visa requirements., Extract required/preferred skills, visa policy, and years of experience., asyncio (+2 more)

### Community 61 - "submit_feedback"
Cohesion: 0.25
Nodes (9): FeedbackRequest, FeedbackResponse, BaseModel, CurrentUser, post, Payload for submitting user interview and coaching feedback. Attributes:…, Response confirming synthesized prompt weight adjustments. Attributes:…, Synthesize candidate feedback into updated agent prompt weights. Passes… (+1 more)

### Community 62 - ".dispatch"
Cohesion: 0.25
Nodes (7): CorrelationIdMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, FastAPI middleware to extract or inject X-Correlation-ID and log HTTP timing.…, Process incoming request, track latency, and attach correlation header.

### Community 63 - ".with_structured_output"
Cohesion: 0.25
Nodes (5): Any, Return the next simulated response or repeat the terminal entry., Produce a runnable chain that validates simulated JSON into a Pydantic model.…, BaseMessage, Runnable

### Community 64 - "job_listing.py"
Cohesion: 0.23
Nodes (10): app_models_application, app_models_base, app_models_company_dossier, app_models_ingestion, app_models_user_profile, CVBlock model storing chunked user career achievements and embeddings. Career-…, JobListing model storing raw descriptions, requirements, and metadata. This…, UserAccount, CandidatePersona, PersonaSkill, PersonaCVBlockRel, and… (+2 more)

### Community 66 - "PrometheusMetricsMiddleware"
Cohesion: 0.29
Nodes (6): PrometheusMetricsMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, Middleware recording HTTP request counts and durations into MetricsRegistry.

### Community 67 - "InMemoryRateLimiter"
Cohesion: 0.29
Nodes (4): InMemoryRateLimiter, Thread-safe sliding-window rate limiter keyed by client identifier., Check if the key exceeded limit within window_sec. Returns: (is_limited,…, Reset all rate limit counters (useful in tests).

### Community 68 - "RateLimitMiddleware"
Cohesion: 0.29
Nodes (6): BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, RateLimitMiddleware, HTTP middleware enforcing client IP rate limits on Career-OS routes.

### Community 69 - "scrub_pii"
Cohesion: 0.21
Nodes (8): Sanitize emails, phone numbers, and street addresses from prompt text.…, scrub_pii(), Test suite for regex sanitization of prompt inputs and outputs., Emails and phone numbers must be redacted., Street addresses must be replaced with redaction tokens., Technical skills, frameworks, and architecture terms must be untouched., Empty or falsy strings must return cleanly., TestPIIScrubbing

### Community 70 - "AuthModal.jsx"
Cohesion: 0.67
Nodes (4): AuthModal(), handleSubmit(), login(), register()

### Community 71 - "JobDiagnosticModal.jsx"
Cohesion: 0.53
Nodes (4): JobDiagnosticModal(), loadDiagnostics(), getJobDiagnostics(), mockDiagnosticData

### Community 72 - "skill_graph.py"
Cohesion: 0.15
Nodes (19): _stream1_score(), _build_transitive_matrix(), compute_asymmetric_skill_score(), expand_implied_skills(), get_skill_idf_weight(), get_transfer_weight(), normalize_skill(), Asymmetric Skill Graph, Directional Transfer Matrix, and IDF Specificity… (+11 more)

### Community 74 - "parse_document_upload"
Cohesion: 0.22
Nodes (9): parse_document_upload(), parse_pasted_text(), ParseTextRequest, post, Parse an uploaded resume file (PDF, DOCX) and return structured staged data., Parse raw resume or LinkedIn text pasted by candidate., Payload for text-based resume or LinkedIn paste., File (+1 more)

### Community 75 - "TestCORSExposeHeaders"
Cohesion: 0.50
Nodes (3): Test suite for CORS X-Correlation-ID exposure., Settings must configure CORS_EXPOSE_HEADERS with X-Correlation-ID., TestCORSExposeHeaders

### Community 90 - "lifespan"
Cohesion: 0.20
Nodes (10): flush_tracing(), Initialize OpenTelemetry TracerProvider with Phoenix OTLP HTTP exporter and…, Flush pending spans and cleanly shut down the OpenTelemetry provider., setup_tracing(), main(), CLI entrypoint for running the worker., lifespan(), FastAPI (+2 more)

### Community 91 - "get_db"
Cohesion: 0.24
Nodes (10): get_db(), AsyncSession, Yield an async database session for use as a FastAPI dependency. Usage in a…, asyncio, AsyncSession, Verify complete onboarding API flow, persona switcher, and block CRUD., Verify persona editing, renaming, case-insensitive duplicate guards, and…, test_candidate_onboarding_and_persona_api_flow() (+2 more)

### Community 92 - "hash_password"
Cohesion: 0.33
Nodes (6): hash_password(), Generate a salted bcrypt hash of a plaintext password. Args: plain_password:…, Verify whether a plaintext password matches a stored bcrypt hash. Args:…, verify_password(), Verify bcrypt password hashing and verification., test_hash_and_verify_password()

### Community 93 - "Database Architecture & Pure SQL Migrations Guide"
Cohesion: 0.18
Nodes (10): 1. Directory Structure, 2. Why Pure SQL Instead of Alembic?, 3.1 `uuid-ossp`, 3.2 `vector` (`pgvector`), 3. Required PostgreSQL Extensions, 4. Entity-Relationship & Table Overview, 5.1 Common Commands, 5.2 Tracking Table & Tampering Protection (+2 more)

### Community 94 - "Engineering Specification: Advanced Skill Representation, Hybrid Matching Engine, and Evaluation Suite"
Cohesion: 0.18
Nodes (10): 1.1 Flaws in Baseline Matching Architecture, 1. Executive Summary & Problem Analysis, 2. Gap Analysis: System Requirements Previously Missing, 3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 3.2 Stage 2: Unified Multi-Factor Reranking Equation, 3. Upgraded Matching Engine Specification, 4. Evaluation Toolkit & Verification Suite, 5. Implementation Roadmap (+2 more)

### Community 95 - "metrics_endpoint"
Cohesion: 0.33
Nodes (6): health_check(), metrics_endpoint(), get, Response, Export Prometheus text format application and connection pool metrics., Return service health and database connectivity status. Executes a lightweight…

### Community 96 - "tracing.py"
Cohesion: 0.20
Nodes (9): OpenTelemetry and Arize Phoenix tracing subsystem for Career-OS. Provides: -…, hmac, openinference_instrumentation_langchain, opentelemetry, opentelemetry_context, opentelemetry_exporter_otlp_proto_http_trace_exporter, opentelemetry_sdk_trace, opentelemetry_sdk_trace_export (+1 more)

### Community 97 - "test_security_headers.py"
Cohesion: 0.20
Nodes (9): Unit tests for HTTP security headers and CORS policy enforcement., Verify security headers are preserved on 4xx/5xx error responses., Verify CORS preflight returns configured allowed origin, methods, and headers., Verify untrusted origins outside CORS_ORIGINS do not receive allow headers., Verify OWASP security headers are attached to standard HTTP responses., test_cors_disallows_untrusted_origin(), test_cors_preflight_allowed_origin(), test_security_headers_present_on_error_responses() (+1 more)

### Community 98 - "test_rate_limit.py"
Cohesion: 0.22
Nodes (8): clean_rate_limiter(), fixture, Verify that requests below the rate limit succeed with RFC 6585 headers., Verify that requests exceeding threshold return 429 Too Many Requests., Verify 429 response structure matches RFC 7807 problem details., test_rate_limit_middleware_returns_rfc7807_problem(), test_rate_limiter_allows_requests_under_threshold(), test_rate_limiter_blocks_and_returns_429_when_exceeded()

### Community 99 - "collections_abc"
Cohesion: 0.25
Nodes (7): db_session(), AsyncSession, fixture, Pytest fixtures for Career-OS testing. Provides in-memory SQLite async database…, Provide an isolated in-memory SQLite database session for unit tests. Creates…, collections_abc, pytest_asyncio

### Community 100 - ".get_usage"
Cohesion: 0.40
Nodes (3): Any, Retrieve current usage and limits for a provider., Fetch recruiter or hiring team contact records.

### Community 101 - "test_health.py"
Cohesion: 0.40
Nodes (4): asyncio, Integration tests for FastAPI health check endpoint., Verify GET /health returns HTTP 200 and expected status payload., test_health_check_endpoint()

### Community 102 - "build_run_config"
Cohesion: 0.29
Nodes (6): build_run_config(), RunnableConfig, Construct a unified LangGraph RunnableConfig enriched with correlation, subject…, Test suite for build_run_config helper., build_run_config must construct correct metadata and tags., TestRunnableConfigBuilder

### Community 103 - "fastapi_testclient"
Cohesion: 0.29
Nodes (6): Unit tests for Prometheus metrics registry and /metrics endpoint., Verify that /metrics exports valid Prometheus text format., Verify metrics_registry records requests and computes summaries., test_metrics_endpoint_exports_prometheus_format(), test_metrics_registry_records_durations(), fastapi_testclient

### Community 104 - "_scrub_attribute_value"
Cohesion: 0.33
Nodes (5): Any, Sanitize span attribute dictionaries before serialization., Recursively scrub strings within span attribute values., _scrub_attribute_value(), ReadableSpan

### Community 105 - "CompanyIntelExtractionSchema"
Cohesion: 0.67
Nodes (3): CompanyIntelExtractionSchema, BaseModel, Structured extraction of company architecture and engineering culture.

### Community 106 - "commit_onboarding"
Cohesion: 0.40
Nodes (5): commit_onboarding(), OnboardingCommitRequest, Any, Commit verified onboarding qualifications to account, personas, and CV blocks., Payload for committing verified onboarding profile data to database.

### Community 107 - "test_graph_recursion.py"
Cohesion: 0.25
Nodes (7): asyncio, Unit tests for LangGraph recursion bounds and execution limit guards., Verify GRAPH_RECURSION_LIMIT is configured and exceeds single pass length., Verify that setting a low recursion limit raises GraphRecursionError., test_pipeline_graph_enforces_recursion_limit(), test_settings_defines_graph_recursion_limit(), langgraph_errors

### Community 109 - "0003_domain_alignment_schema.sql"
Cohesion: 0.40
Nodes (4): cv_block, idx_cv_block_industry_tags_gin, idx_job_listing_industry_vertical, job_listing

### Community 110 - "CompanyIntelProviderPort"
Cohesion: 0.50
Nodes (3): CompanyIntelProviderPort, Port for sourcing company dossier intelligence with provenance., Retrieve verified company intelligence.

## Knowledge Gaps
- **81 isolated node(s):** `1.1 Flaws in Baseline Matching Architecture`, `2. Gap Analysis: System Requirements Previously Missing`, `3.1 Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF)`, `Context & Domain Alignment Blending ($S_{\text{context}}$)`, `4. Evaluation Toolkit & Verification Suite` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 977 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `JobListing` connect `JobListing` to `job_listing.py`, `typing`, `sqlalchemy`, `adapters/ats.py`, `worker.py`, `migrate.py`, `create_or_update_application`, `models.py`, `jobs.py`, `CandidatePersona`, `api.py`, `LocalJobSourceService`, `test_verification.py`, `IngestionQueue`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `MockChatModel` connect `get_llm` to `test_reflector_llm.py`, `test_ats_llm.py`, `test_coach_llm.py`, `llm.py`, `.with_structured_output`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `typing`, `pytest`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AgentState` (e.g. with `create_interview_graph()` and `create_pipeline_graph()`) actually correct?**
  _`AgentState` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `JobListing` (e.g. with `create_or_update_application()` and `list_applications()`) actually correct?**
  _`JobListing` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `CVBlock` (e.g. with `search_cv_blocks()` and `commit_onboarding()`) actually correct?**
  _`CVBlock` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `CandidatePersona` (e.g. with `register_account()` and `_serialize_persona()`) actually correct?**
  _`CandidatePersona` has 21 INFERRED edges - model-reasoned connections that need verification._