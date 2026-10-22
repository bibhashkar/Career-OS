# Graph Report - career-os  (2026-10-22)

## Corpus Check
- 190 files · ~115,134 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .conf 1)

## Summary
- 1930 nodes · 4438 edges · 118 communities (99 shown, 19 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 358 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c9abb00`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- create_cv_block
- VisaSponsorshipStatus
- main.py
- JobListing
- jobs.py
- set_test_llm
- migrate.py
- core/auth.py
- test_matching.py
- search_cv_blocks
- embeddings.py
- candidates.py
- ledger.py
- export_tailored_cv
- test_candidates.py
- ADR-008: High-Probability Job Matching, Two-Stage Retrieval & Fault-Tolerant Ranking
- package.json
- Settings
- typing
- AgentState
- test_agent_grounding.py
- test_verification_detects_salary_and_status_discrepancy
- execute_with_retry
- tracing.py
- sanitize_text
- graph.py
- IngestionQueue
- PersonaManagementModal
- llm.py
- test_api_routes.py
- api/auth.py
- fastapi_testclient
- react
- errors.py
- LangGraph Orchestrator
- LocationNormalizer
- get_job_matches
- ATSBoard
- CVBlock
- Dashboard.jsx
- create_or_update_application
- test_auth.py
- paste_job_text
- OnboardingWizard
- diagnostics.py
- test_auth_register_login_and_me_flow
- test_api_endpoints.py
- test_honesty.py
- test_cv_export.py
- devDependencies
- crawl_jobs.py
- parse_generic_resume_text
- reset_test_llm
- App.jsx
- core/security.py
- derive_subject_id
- MetricsRegistry
- test_coach_llm.py
- InterviewSimulator.jsx
- test_payload_limits.py
- tailor_node
- submit_feedback
- test_logging.py
- MockChatModel
- JobVerificationPort
- matching.py
- PrometheusMetricsMiddleware
- InMemoryRateLimiter
- RateLimitMiddleware
- asyncio
- api.js
- JobDiagnosticModal.jsx
- retrieve_and_rank_jobs
- generate_deterministic_embedding
- parse_resume_bytes
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
- test_graph_checkpointer.py
- get_db
- hash_password
- fetch_company_news_rss
- .acquire_permit
- metrics_endpoint
- dependencies
- scripts
- vite.config.js
- ParsedCVChunkSchema
- .get_usage
- pytest
- ATSAnalysisSchema
- ReflectorDirectiveSchema
- merge_list
- CompanyIntelExtractionSchema
- @testing-library/jest-dom
- test_graph_recursion.py
- calculate_compensation_score
- test_job_matching_and_diagnostics_api_flow
- TestMetricsAndLoopGuards
- ._process_one_task
- calculate_archetype_score
- calculate_freshness_score
- calculate_seniority_score
- BaseModel
- datetime
- asyncio

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 64 edges
2. `JobListing` - 42 edges
3. `DiscoveredJobDTO` - 36 edges
4. `Base` - 33 edges
5. `react` - 32 edges
6. `BoardSyncService` - 29 edges
7. `AshbyAdapter` - 28 edges
8. `GreenhouseAdapter` - 28 edges
9. `LeverAdapter` - 28 edges
10. `ATSBoard` - 26 edges

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

## Communities (118 total, 19 thin omitted)

### Community 0 - "create_cv_block"
Cohesion: 0.15
Nodes (25): create_cv_block(), CVBlockResponse, delete_cv_block(), delete_persona(), get_candidate_audit(), get_persona_benchmark(), _get_user_uuid(), list_cv_blocks() (+17 more)

### Community 1 - "VisaSponsorshipStatus"
Cohesion: 0.11
Nodes (26): classify_visa_sponsorship(), extract_deterministic_requirements(), extract_years_of_experience(), Deterministic requirements extraction and visa status classification. Pass 1 of…, Classify visa sponsorship as YES, NO, or UNKNOWN based on text evidence.…, Extract minimum required years of experience from description text., Deterministic Pass 1: Extracts skills, minimum experience, and visa status…, HybridRequirementsExtractor (+18 more)

### Community 2 - "main.py"
Cohesion: 0.10
Nodes (30): Applicant Tracking System (ATS) agent node and keyword gap evaluation. In…, Reflector agent node synthesizing candidate feedback into quantitative…, Shared state schema and reducers for LangGraph multi-agent workflows. LangGraph…, CV generation and ATS evaluation loop API endpoints. This router exposes the…, User review and prompt weight reflection API endpoints. This router manages…, interview_websocket_endpoint(), websocket, Bi-directional WebSocket endpoint for stateful mock interview coaching. This… (+22 more)

### Community 3 - "JobListing"
Cohesion: 0.07
Nodes (65): Application tracker API endpoints. Enables candidates to save job listings and…, Application, Application model storing candidate job application tracker statuses. Tracks…, Candidate application tracking record. Attributes: user_profile_id: Foreign key…, Base, datetime, Base SQLAlchemy declarative model and common audit mixins. This module provides…, Return timezone-aware current UTC datetime. (+57 more)

### Community 4 - "jobs.py"
Cohesion: 0.06
Nodes (65): ingest_job_from_url(), Job search, manual ingestion, and company intelligence API endpoints. This…, Ingest a job posting from a supported careers URL (Greenhouse, Lever, Ashby).…, AshbyAdapter, GreenhouseAdapter, LeverAdapter, AsyncClient, Tier-1 ATS client adapters for Greenhouse, Lever, Ashby, Workable, and… (+57 more)

### Community 5 - "set_test_llm"
Cohesion: 0.10
Nodes (21): BaseChatModel, Override the model instance returned by ``get_llm`` for testing. Args: model:…, set_test_llm(), Simulated failing LLM to verify resilience on error., FailingChatModel, asyncio, BaseChatModel, Unit tests for company intel LLM tech stack extraction and resilience. (+13 more)

### Community 6 - "migrate.py"
Cohesion: 0.09
Nodes (35): argparse, Unit tests for Career-OS pure SQL migration runner and baseline integrity., Verify 0001_initial_schema.sql is discovered in migrations directory., Verify initial schema file contains required extensions, tables, and seeds., Verify SHA-256 calculation matches file hash., Verify show_status displays cleanly with mock connection., test_checksum_calculation(), test_initial_schema_file_contents_and_extensions() (+27 more)

### Community 7 - "core/auth.py"
Cohesion: 0.11
Nodes (23): authenticate_websocket(), _b64_decode(), _b64_encode(), decode_access_token(), get_current_user(), BaseModel, Depends, Request (+15 more)

### Community 8 - "test_matching.py"
Cohesion: 0.14
Nodes (14): app_core_auth, app_core_database, app_models_ingestion, calculate_probabilistic_gate(), Compute Bayesian uncertainty gate G_prob and hard-pass eligibility. Rules: -…, Unit and integration tests for Two-Stage Matching Engine & Three-Tier…, Verify cross-technology equivalence discovery (e.g. GCP -> AWS)., Critical ADR-002 verification: Missing visa sponsorship MUST NOT result in 0.0… (+6 more)

### Community 9 - "search_cv_blocks"
Cohesion: 0.15
Nodes (17): Any, AsyncSession, UUID, Retrieve top-k matching CV blocks using pgvector or keyword matching. If an…, search_cv_blocks(), asyncio, Verify job search filters by visa sponsorship when required., Verify company intel tool returns tech stack, news, and business model. (+9 more)

### Community 10 - "embeddings.py"
Cohesion: 0.09
Nodes (32): chunk_cv_text(), embed_text(), embed_texts(), _embedding_cache_key(), get_cached_embedding(), ingest_cv_blocks(), _persist_with_session(), Any (+24 more)

### Community 11 - "candidates.py"
Cohesion: 0.11
Nodes (30): commit_onboarding(), create_persona(), CreateSpecializedPersonaRequest, CVBlockCreateRequest, _get_or_create_account(), OnboardingCommitRequest, parse_pasted_text(), ParseTextRequest (+22 more)

### Community 12 - "ledger.py"
Cohesion: 0.09
Nodes (20): CircuitBreaker, PersistentBudgetLedger, AsyncSession, Persistent rate-limit ledger and circuit breaker implementations. Guarantees…, Circuit breaker tracking consecutive failures and cooldown timers per provider., Check if provider is available or in active cooldown., Reset failure counts upon successful operation., Increment failure counter and trip breaker if threshold exceeded. (+12 more)

### Community 13 - "export_tailored_cv"
Cohesion: 0.13
Nodes (20): CVExportRequest, CVGenerateRequest, CVGenerateResponse, CVIngestRequest, CVIngestResponse, export_tailored_cv(), generate_tailored_cv(), ingest_cv_document() (+12 more)

### Community 14 - "test_candidates.py"
Cohesion: 0.19
Nodes (13): detect_is_linkedin_pdf(), extract_skills_from_text(), Resume and document parsing engine for multi-modal candidate onboarding. This…, Detect whether extracted text conforms to LinkedIn's 'Save to PDF' export…, Match and normalize canonical technical skills using SKILL_TAXONOMY., Unit tests for resume parser and candidate onboarding CRUD APIs., Verify canonical technical skills normalization via SKILL_TAXONOMY., Verify LinkedIn 'Save to PDF' detection and structured parsing. (+5 more)

### Community 15 - "ADR-008: High-Probability Job Matching, Two-Stage Retrieval & Fault-Tolerant Ranking"
Cohesion: 0.11
Nodes (18): 1. Stage 1: Hybrid Inverted Index & Reciprocal Rank Fusion (RRF), 1. Two-Stage Retrieval Pipeline (Galene-Inspired), 2. Fault-Tolerant Parameter & Missing Data Handling, 2. Stage 2: Asymmetric Skill Graph & Specificity Weighting, 3. Real-World Signals: Prestige & Achievement Modeling, 3. Upgraded Multi-Factor Reranking Formula, 4. Compensation Normalization ($S_{\text{comp}}$) & Deduplication, A. Company & Institution Prestige ($S_{\text{prestige}} \in [0.0, 1.0]$) (+10 more)

### Community 16 - "package.json"
Cohesion: 0.14
Nodes (15): name, private, type, version, autoprefixer, axios, eslint, @eslint/js (+7 more)

### Community 17 - "Settings"
Cohesion: 0.08
Nodes (25): Any, Treat blank/empty strings in .env as None for optional API keys., Normalise list settings from multiple env-variable formats. Docker Compose and…, Validate sampling rate is within [0.0, 1.0]., Return True if executing within automated pytest or test environment., Derive DATABASE_URL from POSTGRES_* and validate production constraints., Global application settings resolved from environment variables. Fields map…, Settings (+17 more)

### Community 18 - "typing"
Cohesion: 0.07
Nodes (40): asyncio, fetch_company_intel(), Any, Company intelligence gathering tool with Exa neural search and offline…, Fetch architectural intelligence and background for a target employer. Tries…, External tool integration wrappers for agent nodes. Each module wraps one…, Job search tool integration using JSearch API with hermetic offline fallbacks.…, Semantic vector search helper for CVBlock achievements using pgvector.… (+32 more)

### Community 19 - "AgentState"
Cohesion: 0.07
Nodes (45): Determine whether to route back to tailor_node or terminate the pipeline.…, route_ats(), ats_node(), Any, Score the current CV draft against job criteria and identify keyword gaps.…, profiler_node(), Any, Profiler agent node establishing user constraints and stylistic directives. As… (+37 more)

### Community 20 - "test_agent_grounding.py"
Cohesion: 0.06
Nodes (41): hunter_node(), Any, Hunter agent node discovering, ranking, and selecting target job listings. The…, Execute job board search and semantic pgvector ranking against candidate…, CompanyIntelPort, get_default_company_intel(), get_default_job_source(), JobListingDTO (+33 more)

### Community 21 - "test_verification_detects_salary_and_status_discrepancy"
Cohesion: 0.18
Nodes (14): _get_or_create_test_board(), MockDiscrepancyAdapter, MockNotFoundAdapter, Any, asyncio, AsyncSession, Verify when no secondary listing is found, status='not_found' is recorded., Verify existing verification is returned if within 7 days unless forced. (+6 more)

### Community 22 - "execute_with_retry"
Cohesion: 0.15
Nodes (14): execute_with_retry(), Any, Response, Execute an async HTTP call with bounded retries and exponential backoff. Args:…, asyncio, Unit tests for resilient HTTP client execute_with_retry helper., Verify that successful requests return immediately without additional retries., Verify recovery when initial attempts return transient 503 or 429 errors. (+6 more)

### Community 23 - "tracing.py"
Cohesion: 0.05
Nodes (42): flush_tracing(), PIIScrubbingSpanProcessor, Any, OpenTelemetry and Arize Phoenix tracing subsystem for Career-OS. Provides: -…, Sanitize span attribute dictionaries before serialization., Initialize OpenTelemetry TracerProvider with Phoenix OTLP HTTP exporter and…, Flush pending spans and cleanly shut down the OpenTelemetry provider., Sanitize emails, phone numbers, and street addresses from prompt text.… (+34 more)

### Community 24 - "sanitize_text"
Cohesion: 0.07
Nodes (45): _clean_html_to_text(), Safely decode HTML entities and strip HTML markup into clean text., _fetch_detail(), _fetch_detail(), Any, Strip http/https, www, and trailing slashes for comparison., Verify GitHub org homepage matches company domain and extract top languages.…, Physical work modality. (+37 more)

### Community 25 - "graph.py"
Cohesion: 0.11
Nodes (21): create_interview_graph(), create_pipeline_graph(), create_reflector_graph(), LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing. This…, Build and compile the stateful mock technical interview coaching graph. Each…, Build and compile the feedback synthesis and prompt directive reflection graph.…, Build and compile the end-to-end CV discovery, intelligence, and ATS graph.…, intel_node() (+13 more)

### Community 26 - "IngestionQueue"
Cohesion: 0.13
Nodes (20): IngestionTaskStatus, IngestionTaskType, Supported asynchronous ingestion queue task types., Status lifecycle of an ingestion queue task., IngestionQueue, Any, AsyncSession, datetime (+12 more)

### Community 27 - "PersonaManagementModal"
Cohesion: 0.22
Nodes (13): PersonaManagementModal(), handleCreatePersona(), handleDelete(), handleSaveEdit(), handleSetDefault(), PersonaSwitcher(), handleSelect(), loadPersonas() (+5 more)

### Community 28 - "llm.py"
Cohesion: 0.26
Nodes (8): get_llm(), LLM provider abstraction and hermetic model factory for Career-OS agents. Why…, Resolve and return a configured BaseChatModel instance. Selection Priority: 1.…, Coach agent node managing stateful, interactive mock technical interviews. The…, Tailor agent node querying pgvector and assembling customized CV drafts. Rather…, Hybrid requirements extractor with LLM pass and grounding validation.…, langchain_core_language_models_fake_chat_models, langchain_core_messages

### Community 29 - "test_api_routes.py"
Cohesion: 0.21
Nodes (11): asyncio, Integration tests for Career-OS REST endpoints., Verify POST /api/jobs/search returns enriched jobs with company dossiers., Verify POST /api/cv/generate returns tailored CV draft and ATS score., Verify POST /api/feedback synthesizes prompt weight adjustments., Verify feedback submissions never overwrite or corrupt interview state., test_cv_generate_endpoint(), test_feedback_does_not_pollute_interview_thread_state() (+3 more)

### Community 30 - "api/auth.py"
Cohesion: 0.14
Nodes (26): AuthResponse, get_current_user_profile(), login_account(), LoginRequest, PersonaSummaryResponse, BaseModel, CurrentUser, DatabaseSession (+18 more)

### Community 31 - "fastapi_testclient"
Cohesion: 0.06
Nodes (31): Unit tests for RFC 7807 problem details error handling., Verify 404 responses conform to RFC 7807 application/problem+json., Verify schema validation failures format as RFC 7807 with invalid_params., test_404_not_found_returns_problem_details(), test_422_validation_error_returns_problem_details(), Integration tests for bi-directional WebSocket mock interview endpoint., Verify plain unformatted text frames are treated as candidate message content., Verify WebSocket initializes coaching grounded in target job and company. (+23 more)

### Community 32 - "react"
Cohesion: 0.19
Nodes (13): ATSCard(), CompanyDossierCard(), CVPreview(), SessionHistoryModal(), CVTailorView(), generateCV(), refreshCompanyIntel(), mockAuditData (+5 more)

### Community 33 - "errors.py"
Cohesion: 0.13
Nodes (22): create_problem_response(), http_exception_handler(), Any, Exception, FastAPI, Request, RFC 7807 Problem Details global exception handling. Why RFC 7807? Standard HTTP…, Catch-all handler for unexpected internal exceptions (HTTP 500). Logs full… (+14 more)

### Community 34 - "LangGraph Orchestrator"
Cohesion: 0.11
Nodes (24): API-First Decoupled Architecture, ATSCard Component, ATS Cyclic Feedback Loop, ATS Node, Stateful Career Operating System, Coach Node, CompanyDossier Model, CVBlock Model (+16 more)

### Community 35 - "LocationNormalizer"
Cohesion: 0.18
Nodes (16): LocationNormalizer, Deterministic skills, location, and visa sponsorship taxonomy normalizers. Maps…, Normalizes unstructured location strings into granular geographical fields., Parses immigration and work authorization terms from job descriptions., VisaSponsorshipParser, Tests for LocationNormalizer and VisaSponsorshipParser taxonomy engines., test_location_normalizer_australia(), test_location_normalizer_canada() (+8 more)

### Community 36 - "get_job_matches"
Cohesion: 0.24
Nodes (11): get_job_diagnostics(), get_job_matches(), _get_user_uuid(), JobMatchesResponse, AsyncSession, Depends, get, UUID (+3 more)

### Community 37 - "ATSBoard"
Cohesion: 0.08
Nodes (22): generate_candidate_slugs(), Extract provider and slug from job apply URL and auto-register board. Promotes…, Probe official ATS endpoints for candidate slugs. Only queries official fixed…, Probe whether an ATS board slug exists and is active., Generate normalized candidate board slugs for probing. e.g. 'Stripe, Inc.' ->…, Register a new ATS board in the database if not already present., The ATS provider identity., Ensure an ATSBoard record exists in the database for relational safety. (+14 more)

### Community 38 - "CVBlock"
Cohesion: 0.50
Nodes (4): CVBlock, Stores granular career achievement blocks with pgvector embeddings. Attributes:…, Verify CVBlock stores content, category, metrics, and vector embedding., test_cv_block_embedding_structure()

### Community 39 - "Dashboard.jsx"
Cohesion: 0.18
Nodes (13): ADR-0008, AddJobModal(), JobProvenanceBadge(), Dashboard(), formatRelativeTime(), normalizeJobMatch(), SAMPLE_KEYWORDS, crossCheckJob() (+5 more)

### Community 40 - "create_or_update_application"
Cohesion: 0.15
Nodes (18): ApplicationCreateRequest, ApplicationResponse, ApplicationStatusUpdateRequest, create_or_update_application(), list_applications(), BaseModel, CurrentUser, get (+10 more)

### Community 41 - "test_auth.py"
Cohesion: 0.14
Nodes (18): create_access_token(), Create a signed HS256 JSON Web Token (JWT). Args: user_id: Candidate profile…, Verify Candidate B cannot connect to a thread already owned by Candidate A., Verify standard HS256 JWT encoding and decoding round-trip., Verify expired tokens are rejected with HTTP 401., Verify signature verification fails when token payload is altered., Verify REST endpoints authenticate callers presenting valid Bearer JWT., Verify REST endpoints reject requests with malformed or tampered Bearer token. (+10 more)

### Community 42 - "paste_job_text"
Cohesion: 0.11
Nodes (25): cross_check_job(), _format_job_dict(), IngestJobResponse, IngestJobUrlRequest, JobSearchRequest, JobSearchResponse, paste_job_text(), PasteJobTextRequest (+17 more)

### Community 43 - "OnboardingWizard"
Cohesion: 0.15
Nodes (12): OnboardingWizard(), applyParsedData(), handleFileUpload(), handleFinalSubmit(), handleTextPasteSubmit(), POPULAR_SKILLS, SENIORITY_LEVELS, VISA_STATUS_OPTIONS (+4 more)

### Community 44 - "diagnostics.py"
Cohesion: 0.11
Nodes (30): CandidatePersona, Target career persona representing a specialized professional lens. Every user…, CompetencyDomainScore, DistinctionBadge, generate_holistic_audit(), generate_job_diagnostic(), generate_persona_market_benchmark(), HolisticCandidateAudit (+22 more)

### Community 45 - "test_auth_register_login_and_me_flow"
Cohesion: 0.40
Nodes (4): asyncio, AsyncSession, Verify registration, login, and profile retrieval endpoints., test_auth_register_login_and_me_flow()

### Community 46 - "test_api_endpoints.py"
Cohesion: 0.06
Nodes (34): db_session(), AsyncSession, fixture, Pytest fixtures for Career-OS testing. Provides in-memory SQLite async database…, Provide an isolated in-memory SQLite database session for unit tests. Creates…, patch_db(), asyncio, AsyncSession (+26 more)

### Community 47 - "test_honesty.py"
Cohesion: 0.12
Nodes (17): Any, Search for matching job listings using JSearch API or local fixtures. Queries…, search_jobs(), asyncio, Unit tests validating Phase 0a honesty fixes. Verifies that: 1. Default…, Verify GEMINI_MODEL does not point to retired gemini-1.5-flash., Verify built-in mock jobs are explicitly labeled with data_origin='demo'., Verify built-in mock dossiers are explicitly labeled with data_origin='demo'. (+9 more)

### Community 48 - "test_cv_export.py"
Cohesion: 0.15
Nodes (15): format_cv_as_markdown(), format_cv_as_plaintext(), Any, CV export formatting utility producing clean, ATS-compliant text and Markdown.…, Format a tailored CV draft into a clean, single-column ATS Markdown document., Format a tailored CV draft into pure plain-text suitable for ATS paste-ins., Unit tests for CV export formatting and /api/cv/export endpoint., Verify markdown output contains title, summary, skills, and metrics. (+7 more)

### Community 49 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, eslint, @eslint/js, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+7 more)

### Community 50 - "crawl_jobs.py"
Cohesion: 0.16
Nodes (16): Unit test asserting the integrity and schema validity of data/seed_boards.yaml.…, test_seed_catalog_integrity(), pathlib, crawl_board(), crawl_selected_boards(), _crawl_with_sem(), main(), print_statistics() (+8 more)

### Community 51 - "parse_generic_resume_text"
Cohesion: 0.17
Nodes (16): extract_metrics(), parse_generic_resume_text(), parse_linkedin_text(), ParsedCandidateData, ParsedCVBlock, Any, BaseModel, Extracted candidate profile data synthesized from uploaded document. (+8 more)

### Community 52 - "reset_test_llm"
Cohesion: 0.15
Nodes (16): Clear any active test LLM override, restoring default resolution., reset_test_llm(), asyncio, BaseModel, Unit tests for the Career-OS LLM provider abstraction., Pydantic model for structured output verification., Verify get_llm yields MockChatModel in absence of live credentials., Verify mock structured output parses valid JSON and handles invalid JSON. (+8 more)

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

### Community 60 - "tailor_node"
Cohesion: 0.17
Nodes (12): Any, Retrieve CV blocks from pgvector and assemble tailored CV draft. Reads: -…, tailor_node(), FailingChatModel, asyncio, BaseChatModel, Unit tests for tailor_node LLM synthesis and fallback behavior., Simulated failing LLM to verify resilience on error/timeout. (+4 more)

### Community 61 - "submit_feedback"
Cohesion: 0.25
Nodes (9): FeedbackRequest, FeedbackResponse, BaseModel, CurrentUser, post, Payload for submitting user interview and coaching feedback. Attributes:…, Response confirming synthesized prompt weight adjustments. Attributes:…, Synthesize candidate feedback into updated agent prompt weights. Passes… (+1 more)

### Community 62 - "test_logging.py"
Cohesion: 0.08
Nodes (27): CorrelationIdMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, Set the correlation ID for the current async task context., Format standard library log records as structured single-line JSON. Sanitizes…, Serialize log record attributes to JSON string. (+19 more)

### Community 63 - "MockChatModel"
Cohesion: 0.15
Nodes (11): MockChatModel, Any, Deterministic mock chat model supporting structured outputs and cyclic reuse.…, Return the next simulated response or repeat the terminal entry., Produce a runnable chain that validates simulated JSON into a Pydantic model.…, asyncio, Verify ats_node extracts score and recommendation from LLM structured output., test_ats_node_evaluates_with_structured_output() (+3 more)

### Community 64 - "JobVerificationPort"
Cohesion: 0.15
Nodes (10): DefaultAggregatorCrossCheckAdapter, JobVerificationPort, Any, AsyncSession, UUID, Protocol for secondary aggregator cross-check providers., Query secondary aggregators for matching role. Returns None if not found, or a…, Default cross-check adapter providing hermetic secondary check. In production,… (+2 more)

### Community 65 - "matching.py"
Cohesion: 0.17
Nodes (12): app_agents_tools_embeddings, app_models_cv_block, app_models_job_listing, app_models_user_account, app_services_skill_graph, JobMatchResult, MatchFactorBreakdown, Two-stage candidate-to-job retrieval, ranking, and probability scoring engine.… (+4 more)

### Community 66 - "PrometheusMetricsMiddleware"
Cohesion: 0.29
Nodes (6): PrometheusMetricsMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, Middleware recording HTTP request counts and durations into MetricsRegistry.

### Community 67 - "InMemoryRateLimiter"
Cohesion: 0.29
Nodes (4): InMemoryRateLimiter, Thread-safe sliding-window rate limiter keyed by client identifier., Check if the key exceeded limit within window_sec. Returns: (is_limited,…, Reset all rate limit counters (useful in tests).

### Community 68 - "RateLimitMiddleware"
Cohesion: 0.29
Nodes (6): BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, RateLimitMiddleware, HTTP middleware enforcing client IP rate limits on Career-OS routes.

### Community 69 - "asyncio"
Cohesion: 0.25
Nodes (7): asyncio, test_ashby_adapter_parses_golden_fixture(), test_greenhouse_adapter_parses_golden_fixture(), handler(), test_lever_adapter_parses_golden_fixture(), test_smartrecruiters_adapter_parses_golden_fixture(), test_workable_adapter_parses_golden_fixture()

### Community 70 - "api.js"
Cohesion: 0.26
Nodes (5): AuthModal(), handleSubmit(), apiClient, login(), register()

### Community 71 - "JobDiagnosticModal.jsx"
Cohesion: 0.53
Nodes (4): JobDiagnosticModal(), loadDiagnostics(), getJobDiagnostics(), mockDiagnosticData

### Community 72 - "retrieve_and_rank_jobs"
Cohesion: 0.22
Nodes (10): calculate_achievement_score(), AsyncSession, Extract achievement merit markers (hackathons, open-source, publications).…, Stage 1 Hybrid Inverted Index & Reciprocal Rank Fusion (RRF) Retrieval. Defeats…, Execute two-stage job retrieval, reranking, and persistent caching. Stage 1:…, retrieve_and_rank_jobs(), retrieve_stage1_candidates(), CandidatePersona (+2 more)

### Community 73 - "generate_deterministic_embedding"
Cohesion: 0.20
Nodes (12): Any, generate_deterministic_embedding(), Generate a deterministic, unit-normalized vector for hermetic testing. Uses…, calculate_semantic_top3_score(), _cosine_similarity(), Compute cosine similarity between two float vectors., Extract list[float] from vector column or generate deterministic embedding., Calculate Top-3 Block Max-Sim semantic score S_semantic. Eliminates the double-… (+4 more)

### Community 74 - "parse_resume_bytes"
Cohesion: 0.18
Nodes (12): parse_document_upload(), Parse an uploaded resume file (PDF, DOCX) and return structured staged data., extract_text_from_docx(), extract_text_from_pdf(), parse_resume_bytes(), Extract positional text from PDF bytes using pdfplumber., Extract structured text from Word DOCX bytes using python-docx., Dispatch file bytes to appropriate extraction parser based on filename… (+4 more)

### Community 75 - "TestCORSExposeHeaders"
Cohesion: 0.50
Nodes (3): Test suite for CORS X-Correlation-ID exposure., Settings must configure CORS_EXPOSE_HEADERS with X-Correlation-ID., TestCORSExposeHeaders

### Community 90 - "test_graph_checkpointer.py"
Cohesion: 0.13
Nodes (19): AsyncPostgresSaver, close_postgres_saver(), init_postgres_saver(), Initialize persistent AsyncPostgresSaver and attach it to graph applications.…, Close the underlying PostgreSQL connection pool on shutdown., init_vector_extension(), Create the pgvector extension in PostgreSQL if it does not already exist.…, lifespan() (+11 more)

### Community 91 - "get_db"
Cohesion: 0.24
Nodes (10): get_db(), AsyncSession, Yield an async database session for use as a FastAPI dependency. Usage in a…, asyncio, AsyncSession, Verify complete onboarding API flow, persona switcher, and block CRUD., Verify persona editing, renaming, case-insensitive duplicate guards, and…, test_candidate_onboarding_and_persona_api_flow() (+2 more)

### Community 92 - "hash_password"
Cohesion: 0.33
Nodes (6): hash_password(), Generate a salted bcrypt hash of a plaintext password. Args: plain_password:…, Verify whether a plaintext password matches a stored bcrypt hash. Args:…, verify_password(), Verify bcrypt password hashing and verification., test_hash_and_verify_password()

### Community 93 - "fetch_company_news_rss"
Cohesion: 0.22
Nodes (9): fetch_company_news_rss(), Any, AsyncClient, Fetch recent dated news items from Google News RSS. Returns list of dicts:…, asyncio, test_fetch_company_news_rss_parses_feed(), test_github_org_verifier_rejects_mismatched_domain(), test_github_org_verifier_validates_matching_domain() (+1 more)

### Community 94 - ".acquire_permit"
Cohesion: 0.25
Nodes (5): Any, Get current usage stats for a provider., Resolve configured limits from Settings., Derive period bucket key (YYYY-MM-DD for daily or YYYY-MM-DD-HH for hourly)., Atomically reserve request permits. Returns True if granted, False if exceeded.

### Community 95 - "metrics_endpoint"
Cohesion: 0.33
Nodes (6): health_check(), metrics_endpoint(), get, Response, Export Prometheus text format application and connection pool metrics., Return service health and database connectivity status. Executes a lightweight…

### Community 96 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, axios, lucide-react, react, react-dom, react-router-dom

### Community 97 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 98 - "vite.config.js"
Cohesion: 0.33
Nodes (5): __dirname, ref_node_path, ref_node_url, vite, @vitejs/plugin-react

### Community 99 - "ParsedCVChunkSchema"
Cohesion: 0.40
Nodes (5): ParsedCVChunkSchema, ParsedCVDocumentSchema, BaseModel, Structured extraction of an individual CV achievement block., List of extracted career achievement blocks from resume text.

### Community 100 - ".get_usage"
Cohesion: 0.40
Nodes (3): Any, Retrieve current usage and limits for a provider., Fetch recruiter or hiring team contact records.

### Community 101 - "pytest"
Cohesion: 0.33
Nodes (5): asyncio, Integration tests for FastAPI health check endpoint., Verify GET /health returns HTTP 200 and expected status payload., test_health_check_endpoint(), pytest

### Community 102 - "ATSAnalysisSchema"
Cohesion: 0.67
Nodes (3): ATSAnalysisSchema, BaseModel, Structured ATS evaluation produced via LLM.

### Community 103 - "ReflectorDirectiveSchema"
Cohesion: 0.67
Nodes (3): BaseModel, Structured prompt weights extracted from qualitative user feedback., ReflectorDirectiveSchema

### Community 104 - "merge_list"
Cohesion: 0.67
Nodes (3): merge_list(), Any, Append incoming list items to the existing state list. Used as a LangGraph…

### Community 105 - "CompanyIntelExtractionSchema"
Cohesion: 0.67
Nodes (3): CompanyIntelExtractionSchema, BaseModel, Structured extraction of company architecture and engineering culture.

### Community 107 - "test_graph_recursion.py"
Cohesion: 0.25
Nodes (7): asyncio, Unit tests for LangGraph recursion bounds and execution limit guards., Verify GRAPH_RECURSION_LIMIT is configured and exceeds single pass length., Verify that setting a low recursion limit raises GraphRecursionError., test_pipeline_graph_enforces_recursion_limit(), test_settings_defines_graph_recursion_limit(), langgraph_errors

### Community 108 - "calculate_compensation_score"
Cohesion: 0.38
Nodes (7): calculate_compensation_score(), normalize_job_compensation(), Extract annualized USD base salary bounds (min_salary, max_salary,…, Calculate compensation feasibility S_comp with exponential shortfall penalty.…, Verify salary extraction, prevailing wage fallback, and exponential penalty., test_compensation_normalization_and_exponential_penalty(), JobListing

### Community 109 - "test_job_matching_and_diagnostics_api_flow"
Cohesion: 0.33
Nodes (5): AsyncSession, Integration test verifying /api/jobs/matches, Tier 0 Audit, and Tier 1…, Verify Stage 1 RRF retrieves older, high-match jobs even when newer low-…, test_job_matching_and_diagnostics_api_flow(), test_stage1_rrf_prevents_recency_starvation()

### Community 110 - "TestMetricsAndLoopGuards"
Cohesion: 0.33
Nodes (4): Test suite for agent runs and ATS loop exhaustion metrics., record_agent_run must track execution counts and average latencies., route_ats tripping revision bounds must increment exhaustion metric., TestMetricsAndLoopGuards

### Community 112 - "calculate_archetype_score"
Cohesion: 0.50
Nodes (4): calculate_archetype_score(), Calculate job-specific archetype alignment S_archetype. Eliminates Job-…, Verify S_archetype produces job-discriminating scores across company…, test_archetype_alignment_job_variance()

### Community 113 - "calculate_freshness_score"
Cohesion: 0.50
Nodes (4): calculate_freshness_score(), Calculate application timing advantage based on listing activation recency.…, Verify decay scoring reflecting the 3.8x recruiter callback rate window., test_calculate_freshness_score()

### Community 114 - "calculate_seniority_score"
Cohesion: 0.50
Nodes (4): calculate_seniority_score(), Calibrate seniority level alignment between candidate and role., Verify seniority calibration and required years alignment., test_calculate_seniority_score()

## Knowledge Gaps
- **67 isolated node(s):** `Context`, `Stage 1: Deterministic SQL Pre-Filter (Broad Candidate Pool Selection)`, `Stage 2: Precision Multi-Factor Reranker (Acceptance Probability)`, `2. Fault-Tolerant Parameter & Missing Data Handling`, `A. Company & Institution Prestige ($S_{\text{prestige}} \in [0.0, 1.0]$)` (+62 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 914 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentState` connect `AgentState` to `main.py`, `set_test_llm`, `export_tailored_cv`, `tailor_node`, `test_honesty.py`, `TestMetricsAndLoopGuards`, `MockChatModel`, `test_agent_grounding.py`, `tracing.py`, `graph.py`, `test_graph_checkpointer.py`, `llm.py`, `submit_feedback`, `test_coach_llm.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `fetch_company_intel()` connect `typing` to `main.py`, `jobs.py`, `set_test_llm`, `search_cv_blocks`, `paste_job_text`, `test_honesty.py`, `execute_with_retry`, `llm.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AgentState` (e.g. with `create_interview_graph()` and `create_pipeline_graph()`) actually correct?**
  _`AgentState` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `JobListing` (e.g. with `create_or_update_application()` and `list_applications()`) actually correct?**
  _`JobListing` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `DiscoveredJobDTO` (e.g. with `AshbyAdapter` and `GreenhouseAdapter`) actually correct?**
  _`DiscoveredJobDTO` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Context`, `Stage 1: Deterministic SQL Pre-Filter (Broad Candidate Pool Selection)`, `Stage 2: Precision Multi-Factor Reranker (Acceptance Probability)` to the rest of the system?**
  _67 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `VisaSponsorshipStatus` be split into smaller, more focused modules?**
  _Cohesion score 0.10984848484848485 - nodes in this community are weakly interconnected._