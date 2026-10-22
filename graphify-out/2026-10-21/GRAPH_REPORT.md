# Graph Report - career-os  (2026-10-15)

## Corpus Check
- 186 files · ~107,597 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 7, .example 2, .conf 1)

## Summary
- 1872 nodes · 4375 edges · 107 communities (92 shown, 15 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 358 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1622c5fe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_security.py
- HybridRequirementsExtractor
- test_observability.py
- JobListing
- jobs.py
- fetch_company_intel
- migrate.py
- core/auth.py
- test_matching.py
- search_jobs
- embeddings.py
- candidates.py
- provider.py
- cv.py
- test_candidates.py
- tracing.py
- package.json
- Settings
- worker.py
- AgentState
- VisaSponsorshipStatus
- test_verification.py
- execute_with_retry
- PIIScrubbingSpanProcessor
- DiscoveredJobDTO
- graph.py
- IngestionQueue
- PersonaManagementModal
- typing
- pytest
- api/auth.py
- test_interview_ws.py
- react
- errors.py
- LangGraph Orchestrator
- test_agent_grounding.py
- UserAccount
- ATSBoard
- test_models.py
- Dashboard.jsx
- create_or_update_application
- test_auth.py
- ingest_job_from_url
- OnboardingWizard
- diagnostics.py
- test_auth_register_login_and_me_flow
- main.py
- test_ats_llm.py
- test_cv_export.py
- devDependencies
- FailingChatModel
- parse_generic_resume_text
- conftest.py
- App.jsx
- core/security.py
- derive_subject_id
- MetricsRegistry
- test_coach_llm.py
- InterviewSimulator.jsx
- fastapi_testclient
- test_security_headers.py
- submit_feedback
- test_logging.py
- .with_structured_output
- .dispatch
- scrub_pii
- PrometheusMetricsMiddleware
- InMemoryRateLimiter
- RateLimitMiddleware
- asyncio
- api.js
- JobDiagnosticModal.jsx
- patch_db
- setup_tracing
- ingestion/security.py
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
- test_close_postgres_saver_is_idempotent
- BaseModel
- hash_password
- _scrub_attribute_value
- parse_ats_url
- metrics_endpoint
- dependencies
- scripts
- vite.config.js
- ParsedCVChunkSchema
- .get_usage
- test_health.py
- ATSAnalysisSchema
- ReflectorDirectiveSchema
- merge_list
- CompanyIntelExtractionSchema
- @testing-library/jest-dom

## God Nodes (most connected - your core abstractions)
1. `AgentState` - 64 edges
2. `JobListing` - 46 edges
3. `DiscoveredJobDTO` - 36 edges
4. `Base` - 33 edges
5. `CVBlock` - 32 edges
6. `react` - 32 edges
7. `CandidatePersona` - 30 edges
8. `BoardSyncService` - 29 edges
9. `AshbyAdapter` - 28 edges
10. `GreenhouseAdapter` - 28 edges

## Surprising Connections (you probably didn't know these)
- `crawl_board()` --uses--> `BoardSyncService`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/ingestion/service.py
- `crawl_selected_boards()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `print_statistics()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `seed_database_catalog()` --uses--> `ATSBoard`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/ingestion.py
- `print_statistics()` --uses--> `JobListing`  [INFERRED]
  scripts/crawl_jobs.py → backend/app/models/job_listing.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Agent Workflow** — master_spec_profiler_node, master_spec_hunter_node, master_spec_intel_node, master_spec_tailor_node, master_spec_ats_node, master_spec_coach_node, master_spec_reflector_node [EXTRACTED 1.00]
- **Frontend Presentation Architecture** — master_spec_dashboard_component, master_spec_ats_card_component, master_spec_interview_simulator_component [EXTRACTED 1.00]
- **Persistence and State Tiers** — master_spec_postgres_saver, master_spec_postgresql_database, master_spec_pgvector_extension [EXTRACTED 1.00]

## Communities (107 total, 15 thin omitted)

### Community 0 - "test_security.py"
Cohesion: 0.23
Nodes (15): Exception, Validate that an external HTTP(S) URL is safe to fetch. Rules: - Scheme must be…, Raised when URL or text fails security validation., SecurityValidationError, validate_and_guard_url(), MonkeyPatch, Unit tests for security sterilization and URL validation (SSRF / malicious…, test_validate_and_guard_url_allows_legitimate_host() (+7 more)

### Community 1 - "HybridRequirementsExtractor"
Cohesion: 0.20
Nodes (7): HybridRequirementsExtractor, Any, Two-pass requirements extraction with grounding validation., Check if a candidate skill from the LLM is grounded in the source text., Port for extracting structured ATS requirements from job descriptions., Extract required/preferred skills, visa policy, and years of experience., RequirementsExtractorPort

### Community 2 - "test_observability.py"
Cohesion: 0.09
Nodes (24): interview_websocket_endpoint(), websocket, Bi-directional WebSocket endpoint for stateful mock interview coaching. This…, Stream interview dialogue bi-directionally keyed on thread_id checkpoint.…, Set the correlation ID for the current async task context., set_correlation_id(), Prometheus metrics collector and instrumentation for Career-OS. Exports…, Sliding-window token bucket rate limiting middleware for FastAPI. Protects… (+16 more)

### Community 3 - "JobListing"
Cohesion: 0.10
Nodes (50): Application tracker API endpoints. Enables candidates to save job listings and…, Application, Application model storing candidate job application tracker statuses. Tracks…, Candidate application tracking record. Attributes: user_profile_id: Foreign key…, Base, datetime, Base SQLAlchemy declarative model and common audit mixins. This module provides…, Return timezone-aware current UTC datetime. (+42 more)

### Community 4 - "jobs.py"
Cohesion: 0.06
Nodes (52): JobSearchRequest, JobSearchResponse, Job search, manual ingestion, and company intelligence API endpoints. This…, Discover jobs using Sync-then-Search architecture: 1. Queries local synced ATS…, Payload for job discovery query with location and visa sponsorship filters., Response payload containing matching jobs and gathered company dossiers., search_and_intel(), AshbyAdapter (+44 more)

### Community 5 - "fetch_company_intel"
Cohesion: 0.06
Nodes (53): MockChatModel, BaseChatModel, Override the model instance returned by ``get_llm`` for testing. Args: model:…, Clear any active test LLM override, restoring default resolution., Deterministic mock chat model supporting structured outputs and cyclic reuse.…, reset_test_llm(), set_test_llm(), Any (+45 more)

### Community 6 - "migrate.py"
Cohesion: 0.06
Nodes (51): argparse, Unit test asserting the integrity and schema validity of data/seed_boards.yaml.…, test_seed_catalog_integrity(), Unit tests for Career-OS pure SQL migration runner and baseline integrity., Verify 0001_initial_schema.sql is discovered in migrations directory., Verify initial schema file contains required extensions, tables, and seeds., Verify SHA-256 calculation matches file hash., Verify show_status displays cleanly with mock connection. (+43 more)

### Community 7 - "core/auth.py"
Cohesion: 0.11
Nodes (22): authenticate_websocket(), _b64_decode(), _b64_encode(), decode_access_token(), get_current_user(), BaseModel, Depends, Request (+14 more)

### Community 8 - "test_matching.py"
Cohesion: 0.08
Nodes (37): CVBlock, Stores granular career achievement blocks with pgvector embeddings. Attributes:…, calculate_achievement_score(), calculate_freshness_score(), calculate_prestige_score(), calculate_probabilistic_gate(), calculate_seniority_score(), calculate_skill_overlap() (+29 more)

### Community 9 - "search_jobs"
Cohesion: 0.12
Nodes (20): Any, Search for matching job listings using JSearch API or local fixtures. Queries…, search_jobs(), Any, AsyncSession, UUID, Retrieve top-k matching CV blocks using pgvector or keyword matching. If an…, search_cv_blocks() (+12 more)

### Community 10 - "embeddings.py"
Cohesion: 0.09
Nodes (34): chunk_cv_text(), embed_text(), embed_texts(), _embedding_cache_key(), generate_deterministic_embedding(), get_cached_embedding(), ingest_cv_blocks(), _persist_with_session() (+26 more)

### Community 11 - "candidates.py"
Cohesion: 0.09
Nodes (49): commit_onboarding(), create_cv_block(), create_persona(), CreateSpecializedPersonaRequest, CVBlockCreateRequest, CVBlockResponse, delete_cv_block(), delete_persona() (+41 more)

### Community 12 - "provider.py"
Cohesion: 0.07
Nodes (30): CircuitBreaker, PersistentBudgetLedger, Any, AsyncSession, Persistent rate-limit ledger and circuit breaker implementations. Guarantees…, Get current usage stats for a provider., Circuit breaker tracking consecutive failures and cooldown timers per provider., Check if provider is available or in active cooldown. (+22 more)

### Community 13 - "cv.py"
Cohesion: 0.15
Nodes (21): CVExportRequest, CVGenerateRequest, CVGenerateResponse, CVIngestRequest, CVIngestResponse, export_tailored_cv(), generate_tailored_cv(), ingest_cv_document() (+13 more)

### Community 14 - "test_candidates.py"
Cohesion: 0.08
Nodes (37): detect_is_linkedin_pdf(), extract_metrics(), extract_skills_from_text(), extract_text_from_docx(), extract_text_from_pdf(), parse_linkedin_text(), parse_resume_bytes(), Any (+29 more)

### Community 15 - "tracing.py"
Cohesion: 0.20
Nodes (9): OpenTelemetry and Arize Phoenix tracing subsystem for Career-OS. Provides: -…, hmac, openinference_instrumentation_langchain, opentelemetry, opentelemetry_context, opentelemetry_exporter_otlp_proto_http_trace_exporter, opentelemetry_sdk_trace, opentelemetry_sdk_trace_export (+1 more)

### Community 16 - "package.json"
Cohesion: 0.14
Nodes (15): name, private, type, version, autoprefixer, axios, eslint, @eslint/js (+7 more)

### Community 17 - "Settings"
Cohesion: 0.07
Nodes (28): Any, Treat blank/empty strings in .env as None for optional API keys., Normalise list settings from multiple env-variable formats. Docker Compose and…, Validate sampling rate is within [0.0, 1.0]., Return True if executing within automated pytest or test environment., Derive DATABASE_URL from POSTGRES_* and validate production constraints., Global application settings resolved from environment variables. Fields map…, Settings (+20 more)

### Community 18 - "worker.py"
Cohesion: 0.07
Nodes (37): Public Ingestion Boundary API & Domain Ports. As specified in ARCHITECTURE…, ProvenanceCompanyIntelProvider, AsyncSession, Provenance-tracked company intelligence provider. Replaces paid Exa / Apollo…, Synthesizes company dossiers with strict source grounding and provenance., Retrieve or refresh company intelligence with field-level provenance., GitHubOrgVerifier, AsyncClient (+29 more)

### Community 19 - "AgentState"
Cohesion: 0.10
Nodes (37): Determine whether to route back to tailor_node or terminate the pipeline.…, route_ats(), profiler_node(), Any, Profiler agent node establishing user constraints and stylistic directives. As…, Evaluate baseline user constraints and establish initial profile context.…, AgentState, Execution state schema shared across all Career-OS LangGraph agent nodes. This… (+29 more)

### Community 20 - "VisaSponsorshipStatus"
Cohesion: 0.06
Nodes (38): CompanyIntelPort, get_default_company_intel(), JobListingDTO, JobSourcePort, LocalJobSourceService, ProvenanceCompanyIntelService, ABC, Any (+30 more)

### Community 21 - "test_verification.py"
Cohesion: 0.09
Nodes (27): DefaultAggregatorCrossCheckAdapter, JobVerificationPort, JobVerificationService, Any, AsyncSession, UUID, Protocol for secondary aggregator cross-check providers., Query secondary aggregators for matching role. Returns None if not found, or a… (+19 more)

### Community 22 - "execute_with_retry"
Cohesion: 0.15
Nodes (14): execute_with_retry(), Any, Response, Execute an async HTTP call with bounded retries and exponential backoff. Args:…, asyncio, Unit tests for resilient HTTP client execute_with_retry helper., Verify that successful requests return immediately without additional retries., Verify recovery when initial attempts return transient 503 or 429 errors. (+6 more)

### Community 23 - "PIIScrubbingSpanProcessor"
Cohesion: 0.18
Nodes (10): PIIScrubbingSpanProcessor, OpenTelemetry SpanProcessor that intercepts span attributes before batch export…, MonkeyPatch, Test suite for OpenTelemetry PIIScrubbingSpanProcessor., SpanProcessor on_end must sanitize string attributes., When PHOENIX_ANONYMIZE_PII is False, attributes must not be modified., TestSpanProcessorSanitization, Context (+2 more)

### Community 24 - "DiscoveredJobDTO"
Cohesion: 0.07
Nodes (41): _clean_html_to_text(), Safely decode HTML entities and strip HTML markup into clean text., _fetch_detail(), _fetch_detail(), Any, Strip http/https, www, and trailing slashes for comparison., Verify GitHub org homepage matches company domain and extract top languages.…, DiscoveredJobDTO (+33 more)

### Community 25 - "graph.py"
Cohesion: 0.13
Nodes (18): create_interview_graph(), create_pipeline_graph(), create_reflector_graph(), LangGraph StateGraph orchestration, ATS cyclic routing, and checkpointing. This…, Build and compile the stateful mock technical interview coaching graph. Each…, Build and compile the feedback synthesis and prompt directive reflection graph.…, Build and compile the end-to-end CV discovery, intelligence, and ATS graph.…, intel_node() (+10 more)

### Community 26 - "IngestionQueue"
Cohesion: 0.11
Nodes (22): IngestionTaskStatus, IngestionTaskType, Supported asynchronous ingestion queue task types., Status lifecycle of an ingestion queue task., IngestionQueue, Any, AsyncSession, datetime (+14 more)

### Community 27 - "PersonaManagementModal"
Cohesion: 0.22
Nodes (13): PersonaManagementModal(), handleCreatePersona(), handleDelete(), handleSaveEdit(), handleSetDefault(), PersonaSwitcher(), handleSelect(), loadPersonas() (+5 more)

### Community 28 - "typing"
Cohesion: 0.08
Nodes (39): asyncio, get_llm(), LLM provider abstraction and hermetic model factory for Career-OS agents. Why…, Resolve and return a configured BaseChatModel instance. Selection Priority: 1.…, Applicant Tracking System (ATS) agent node and keyword gap evaluation. In…, Coach agent node managing stateful, interactive mock technical interviews. The…, Reflector agent node synthesizing candidate feedback into quantitative…, Tailor agent node querying pgvector and assembling customized CV drafts. Rather… (+31 more)

### Community 29 - "pytest"
Cohesion: 0.10
Nodes (21): asyncio, Integration tests for Career-OS REST endpoints., Verify POST /api/jobs/search returns enriched jobs with company dossiers., Verify POST /api/cv/generate returns tailored CV draft and ATS score., Verify POST /api/feedback synthesizes prompt weight adjustments., Verify feedback submissions never overwrite or corrupt interview state., test_cv_generate_endpoint(), test_feedback_does_not_pollute_interview_thread_state() (+13 more)

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
Cohesion: 0.09
Nodes (31): create_problem_response(), http_exception_handler(), Any, Exception, FastAPI, Request, RFC 7807 Problem Details global exception handling. Why RFC 7807? Standard HTTP…, Catch-all handler for unexpected internal exceptions (HTTP 500). Logs full… (+23 more)

### Community 34 - "LangGraph Orchestrator"
Cohesion: 0.11
Nodes (24): API-First Decoupled Architecture, ATSCard Component, ATS Cyclic Feedback Loop, ATS Node, Stateful Career Operating System, Coach Node, CompanyDossier Model, CVBlock Model (+16 more)

### Community 35 - "test_agent_grounding.py"
Cohesion: 0.14
Nodes (18): hunter_node(), Any, Hunter agent node discovering, ranking, and selecting target job listings. The…, Execute job board search and semantic pgvector ranking against candidate…, get_default_job_source(), Return default application-wide JobSourcePort implementation., asyncio, Tests for Deep Agent Integration, Hunter Semantic pgvector Ranking, and ATS… (+10 more)

### Community 36 - "UserAccount"
Cohesion: 0.12
Nodes (20): get_job_diagnostics(), get_job_matches(), _get_user_uuid(), JobMatchesResponse, AsyncSession, Depends, get, UUID (+12 more)

### Community 37 - "ATSBoard"
Cohesion: 0.12
Nodes (21): BoardDiscoveryEngine, generate_candidate_slugs(), ATS Board Discovery & Probing Engine. Discovers and registers new company ATS…, Extract provider and slug from job apply URL and auto-register board. Promotes…, Probe official ATS endpoints for candidate slugs. Only queries official fixed…, Probe whether an ATS board slug exists and is active., Generate normalized candidate board slugs for probing. e.g. 'Stripe, Inc.' ->…, Engine to discover, probe, and register ATS boards with entity protection. (+13 more)

### Community 38 - "test_models.py"
Cohesion: 0.10
Nodes (21): JobMatchCache, PersonaSkill, Normalized technical and domain competency assigned to a candidate persona.…, Persisted match evaluation cache and diagnostics for persona-job pairs. Stores…, Unit tests for SQLAlchemy models structure, relationships, and naming., Verify FeedbackLog stores thread_id, review feedback, and weights., Verify user_profile.cv_blocks enforces strict RESTRICT without delete-orphan., Verify Application model instantiation and default fields. (+13 more)

### Community 39 - "Dashboard.jsx"
Cohesion: 0.18
Nodes (13): ADR-0008, AddJobModal(), JobProvenanceBadge(), Dashboard(), formatRelativeTime(), normalizeJobMatch(), SAMPLE_KEYWORDS, crossCheckJob() (+5 more)

### Community 40 - "create_or_update_application"
Cohesion: 0.15
Nodes (18): ApplicationCreateRequest, ApplicationResponse, ApplicationStatusUpdateRequest, create_or_update_application(), list_applications(), BaseModel, CurrentUser, get (+10 more)

### Community 41 - "test_auth.py"
Cohesion: 0.13
Nodes (19): create_access_token(), Create a signed HS256 JSON Web Token (JWT). Args: user_id: Candidate profile…, Verify Candidate B cannot connect to a thread already owned by Candidate A., Verify standard HS256 JWT encoding and decoding round-trip., Verify expired tokens are rejected with HTTP 401., Verify signature verification fails when token payload is altered., Verify REST endpoints authenticate callers presenting valid Bearer JWT., Verify REST endpoints reject requests with malformed or tampered Bearer token. (+11 more)

### Community 42 - "ingest_job_from_url"
Cohesion: 0.18
Nodes (17): cross_check_job(), _format_job_dict(), ingest_job_from_url(), IngestJobResponse, paste_job_text(), Any, CurrentUser, post (+9 more)

### Community 43 - "OnboardingWizard"
Cohesion: 0.15
Nodes (12): OnboardingWizard(), applyParsedData(), handleFileUpload(), handleFinalSubmit(), handleTextPasteSubmit(), POPULAR_SKILLS, SENIORITY_LEVELS, VISA_STATUS_OPTIONS (+4 more)

### Community 44 - "diagnostics.py"
Cohesion: 0.14
Nodes (24): CandidatePersona, Target career persona representing a specialized professional lens. Every user…, CompetencyDomainScore, DistinctionBadge, generate_holistic_audit(), generate_job_diagnostic(), generate_persona_market_benchmark(), HolisticCandidateAudit (+16 more)

### Community 45 - "test_auth_register_login_and_me_flow"
Cohesion: 0.40
Nodes (4): asyncio, AsyncSession, Verify registration, login, and profile retrieval endpoints., test_auth_register_login_and_me_flow()

### Community 46 - "main.py"
Cohesion: 0.07
Nodes (37): AsyncPostgresSaver, close_postgres_saver(), init_postgres_saver(), Initialize persistent AsyncPostgresSaver and attach it to graph applications.…, Close the underlying PostgreSQL connection pool on shutdown., init_vector_extension(), SQLAlchemy async engine, session factory, and pgvector extension bootstrap.…, Create the pgvector extension in PostgreSQL if it does not already exist.… (+29 more)

### Community 47 - "test_ats_llm.py"
Cohesion: 0.14
Nodes (16): ats_node(), Any, Score the current CV draft against job criteria and identify keyword gaps.…, asyncio, Unit tests for ATS node LLM structured evaluation and threshold routing., Verify ats_node extracts score and recommendation from LLM structured output., Verify ats_node falls back to formula scoring when LLM fails., test_ats_node_evaluates_with_structured_output() (+8 more)

### Community 48 - "test_cv_export.py"
Cohesion: 0.15
Nodes (15): format_cv_as_markdown(), format_cv_as_plaintext(), Any, CV export formatting utility producing clean, ATS-compliant text and Markdown.…, Format a tailored CV draft into a clean, single-column ATS Markdown document., Format a tailored CV draft into pure plain-text suitable for ATS paste-ins., Unit tests for CV export formatting and /api/cv/export endpoint., Verify markdown output contains title, summary, skills, and metrics. (+7 more)

### Community 49 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, autoprefixer, eslint, @eslint/js, eslint-plugin-react, eslint-plugin-react-hooks, eslint-plugin-react-refresh, jsdom (+7 more)

### Community 50 - "FailingChatModel"
Cohesion: 0.15
Nodes (7): FailingChatModel, BaseChatModel, Simulated failing LLM to verify resilience on error., FailingChatModel, BaseChatModel, FailingChatModel, BaseChatModel

### Community 51 - "parse_generic_resume_text"
Cohesion: 0.15
Nodes (15): parse_document_upload(), parse_pasted_text(), ParseTextRequest, Parse an uploaded resume file (PDF, DOCX) and return structured staged data., Parse raw resume or LinkedIn text pasted by candidate., Payload for text-based resume or LinkedIn paste., parse_generic_resume_text(), ParsedCandidateData (+7 more)

### Community 52 - "conftest.py"
Cohesion: 0.29
Nodes (6): db_session(), AsyncSession, fixture, Pytest fixtures for Career-OS testing. Provides in-memory SQLite async database…, Provide an isolated in-memory SQLite database session for unit tests. Creates…, pytest_asyncio

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

### Community 59 - "fastapi_testclient"
Cohesion: 0.12
Nodes (15): Unit tests for Prometheus metrics registry and /metrics endpoint., Verify that /metrics exports valid Prometheus text format., Verify metrics_registry records requests and computes summaries., test_metrics_endpoint_exports_prometheus_format(), test_metrics_registry_records_durations(), Unit tests for REST request payload limits and WebSocket frame size caps., Verify POST /api/cv/ingest rejects resume text exceeding MAX_CV_RAW_TEXT_LENGTH., Verify POST /api/feedback rejects feedback text exceeding… (+7 more)

### Community 60 - "test_security_headers.py"
Cohesion: 0.20
Nodes (9): Unit tests for HTTP security headers and CORS policy enforcement., Verify security headers are preserved on 4xx/5xx error responses., Verify CORS preflight returns configured allowed origin, methods, and headers., Verify untrusted origins outside CORS_ORIGINS do not receive allow headers., Verify OWASP security headers are attached to standard HTTP responses., test_cors_disallows_untrusted_origin(), test_cors_preflight_allowed_origin(), test_security_headers_present_on_error_responses() (+1 more)

### Community 61 - "submit_feedback"
Cohesion: 0.25
Nodes (9): FeedbackRequest, FeedbackResponse, BaseModel, CurrentUser, post, Payload for submitting user interview and coaching feedback. Attributes:…, Response confirming synthesized prompt weight adjustments. Attributes:…, Synthesize candidate feedback into updated agent prompt weights. Passes… (+1 more)

### Community 62 - "test_logging.py"
Cohesion: 0.19
Nodes (13): Format standard library log records as structured single-line JSON. Sanitizes…, Configure application-wide root logger with StructuredJsonFormatter.…, setup_logging(), StructuredJsonFormatter, Unit tests for structured JSON logging and correlation ID middleware., Verify middleware injects X-Correlation-ID if omitted by client., Verify client-supplied X-Correlation-ID is echoed in response., Verify log formatter emits parseable JSON with context metadata. (+5 more)

### Community 63 - ".with_structured_output"
Cohesion: 0.25
Nodes (5): Any, Return the next simulated response or repeat the terminal entry., Produce a runnable chain that validates simulated JSON into a Pydantic model.…, BaseMessage, Runnable

### Community 64 - ".dispatch"
Cohesion: 0.25
Nodes (7): CorrelationIdMiddleware, BaseHTTPMiddleware, Request, RequestResponseEndpoint, Response, FastAPI middleware to extract or inject X-Correlation-ID and log HTTP timing.…, Process incoming request, track latency, and attach correlation header.

### Community 65 - "scrub_pii"
Cohesion: 0.21
Nodes (8): Sanitize emails, phone numbers, and street addresses from prompt text.…, scrub_pii(), Test suite for regex sanitization of prompt inputs and outputs., Emails and phone numbers must be redacted., Street addresses must be replaced with redaction tokens., Technical skills, frameworks, and architecture terms must be untouched., Empty or falsy strings must return cleanly., TestPIIScrubbing

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

### Community 72 - "patch_db"
Cohesion: 0.40
Nodes (4): patch_db(), AsyncSession, fixture, MonkeyPatch

### Community 73 - "setup_tracing"
Cohesion: 0.25
Nodes (7): flush_tracing(), Initialize OpenTelemetry TracerProvider with Phoenix OTLP HTTP exporter and…, Flush pending spans and cleanly shut down the OpenTelemetry provider., setup_tracing(), main(), CLI entrypoint for running the worker., Tracing setup and flush must complete safely without network calls.

### Community 74 - "ingestion/security.py"
Cohesion: 0.29
Nodes (6): Verified GitHub organization crawler and tech stack analyzer. Extracts top…, Security sterilization and validation for direct URLs and pasted user input.…, ipaddress, socket, unicodedata, urllib_parse

### Community 75 - "TestCORSExposeHeaders"
Cohesion: 0.50
Nodes (3): Test suite for CORS X-Correlation-ID exposure., Settings must configure CORS_EXPOSE_HEADERS with X-Correlation-ID., TestCORSExposeHeaders

### Community 90 - "test_close_postgres_saver_is_idempotent"
Cohesion: 0.29
Nodes (7): asyncio, Verify init_postgres_saver gracefully falls back when database is offline., Verify closing postgres saver multiple times does not raise errors., Verify swapping checkpointer preserves state retrieval in graph execution., test_close_postgres_saver_is_idempotent(), test_graph_checkpointer_swap_preserves_execution(), test_init_postgres_saver_handles_unreachable_db()

### Community 91 - "BaseModel"
Cohesion: 0.40
Nodes (6): IngestJobUrlRequest, PasteJobTextRequest, BaseModel, Response payload for company intelligence refresh., Payload for importing a job posting by URL., RefreshCompanyResponse

### Community 92 - "hash_password"
Cohesion: 0.33
Nodes (6): hash_password(), Generate a salted bcrypt hash of a plaintext password. Args: plain_password:…, Verify whether a plaintext password matches a stored bcrypt hash. Args:…, verify_password(), Verify bcrypt password hashing and verification., test_hash_and_verify_password()

### Community 93 - "_scrub_attribute_value"
Cohesion: 0.33
Nodes (5): Any, Sanitize span attribute dictionaries before serialization., Recursively scrub strings within span attribute values., _scrub_attribute_value(), ReadableSpan

### Community 94 - "parse_ats_url"
Cohesion: 0.33
Nodes (6): parse_ats_url(), Parse a known direct ATS job posting or board URL. Returns: tuple of (provider,…, test_parse_ats_url_ashby(), test_parse_ats_url_greenhouse(), test_parse_ats_url_lever(), test_parse_ats_url_unrecognized()

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

### Community 101 - "test_health.py"
Cohesion: 0.40
Nodes (4): asyncio, Integration tests for FastAPI health check endpoint., Verify GET /health returns HTTP 200 and expected status payload., test_health_check_endpoint()

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

## Knowledge Gaps
- **54 isolated node(s):** `axios`, `lucide-react`, `react`, `react-dom`, `react-router-dom` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 883 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentState` connect `AgentState` to `test_observability.py`, `test_agent_grounding.py`, `fetch_company_intel`, `cv.py`, `test_ats_llm.py`, `pytest`, `graph.py`, `test_close_postgres_saver_is_idempotent`, `typing`, `submit_feedback`, `test_coach_llm.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `JobListing` connect `JobListing` to `jobs.py`, `UserAccount`, `test_models.py`, `migrate.py`, `create_or_update_application`, `test_matching.py`, `ingest_job_from_url`, `diagnostics.py`, `worker.py`, `VisaSponsorshipStatus`, `test_verification.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AgentState` (e.g. with `create_interview_graph()` and `create_pipeline_graph()`) actually correct?**
  _`AgentState` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `JobListing` (e.g. with `create_or_update_application()` and `list_applications()`) actually correct?**
  _`JobListing` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `DiscoveredJobDTO` (e.g. with `AshbyAdapter` and `GreenhouseAdapter`) actually correct?**
  _`DiscoveredJobDTO` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `axios`, `lucide-react`, `react` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_observability.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08602150537634409 - nodes in this community are weakly interconnected._