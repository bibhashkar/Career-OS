-- =============================================================================
-- Career-OS: Initial Clean Relational & Semantic Vector Schema
-- Migration: 0001_initial_schema.sql
-- =============================================================================
-- Description:
--   Single canonical baseline schema definition for Career-OS.
--   Enforces strict relational integrity (ON DELETE RESTRICT), granular multi-tier
--   geographic tracking, workplace modality vs. remote jurisdiction separation,
--   multi-jurisdiction visa sponsorship policies, and 1536-dimensional HNSW
--   semantic vector indexing via pgvector.
-- =============================================================================

-- =============================================================================
-- SECTION 1: POSTGRESQL EXTENSIONS BOOTSTRAP
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Extension: uuid-ossp
-- -----------------------------------------------------------------------------
-- Purpose:
--   Provides RFC 4122 compliant version 4 UUID generation functions (uuid_generate_v4()).
-- Rationale in Career-OS:
--   1. Decentralized & Collision-Free IDs:
--      Asynchronous background crawler workers, queue processors, and API services
--      can independently generate unique primary keys before persisting records to
--      PostgreSQL without requiring database roundtrips.
--   2. Security & Anti-Enumeration:
--      Sequential auto-incrementing integer IDs (e.g., /jobs/1, /jobs/2) leak platform
--      velocity and allow trivial scraping attacks. UUIDv4 keys eliminate enumeration risks.
--   3. Idempotent Data Synchronization:
--      Facilitates cross-system synchronization and distributed checkpoint persistence.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- Extension: vector (pgvector)
-- -----------------------------------------------------------------------------
-- Purpose:
--   High-performance vector operations and Approximate Nearest Neighbor (ANN) indexing.
-- Rationale in Career-OS:
--   1. Semantic Resume Synthesis & Matching:
--      Career-OS tailors resumes by matching candidate career accomplishments (cv_block)
--      against target job requisitions using dense 1536-dimensional semantic embeddings.
--   2. Native Vector Distance Operators:
--      Provides native support for cosine distance ('<=>'), allowing fast similarity queries
--      computed as `1 - (embedding <=> target_vector)`.
--   3. In-Database HNSW Indexing:
--      Enables Hierarchical Navigable Small World (HNSW) index structures (m=16, ef_construction=64)
--      for sub-millisecond similarity queries across millions of candidate career blocks
--      without needing external vector database vendors (e.g. Pinecone/Milvus), keeping all candidate
--      data hermetic, transactional, and ACID-compliant within PostgreSQL.
CREATE EXTENSION IF NOT EXISTS vector;


-- =============================================================================
-- SECTION 2: LOOKUP TABLES (REFERENCE TAXONOMY)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: ats_provider
-- Description: Root lookup catalog of supported Applicant Tracking System platforms.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ats_provider (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_base_url VARCHAR(255) NULL,
    auth_type VARCHAR(50) NOT NULL DEFAULT 'public_api',
    default_rate_limit_rps FLOAT NOT NULL DEFAULT 5.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed initial supported ATS providers
INSERT INTO ats_provider (code, name, api_base_url, default_rate_limit_rps) VALUES
    ('greenhouse', 'Greenhouse Software', 'https://boards-api.greenhouse.io/v1/boards', 5.0),
    ('lever', 'Lever Hire', 'https://api.lever.co/v0/postings', 2.0),
    ('ashby', 'Ashby HQ', 'https://api.ashbyhq.com/posting-api/job-board', 3.0),
    ('workable', 'Workable', 'https://apply.workable.com/api/v3/accounts', 2.0),
    ('smartrecruiters', 'SmartRecruiters', 'https://api.smartrecruiters.com/v1/companies', 3.0),
    ('custom', 'Custom Employer Portal', NULL, 1.0)
ON CONFLICT (code) DO NOTHING;

-- -----------------------------------------------------------------------------
-- Table: industry_sector
-- Description: Standardized, snake_case industry taxonomy (strictly no slashes).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS industry_sector (
    code VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed standardized snake_case industry sectors
INSERT INTO industry_sector (code, name) VALUES
    ('hft_quant_trading', 'High-Frequency & Quantitative Trading'),
    ('fintech', 'Financial Technology & Payments'),
    ('healthtech', 'Healthcare & Clinical Systems'),
    ('biotech', 'Life Sciences & Computational Biology'),
    ('ai_ml_infra', 'AI, ML & Compute Infrastructure'),
    ('ai_machine_learning', 'Artificial Intelligence & Machine Learning'),
    ('blockchain_web3', 'Blockchain, Crypto & Web3'),
    ('devtools', 'Developer Tools & Engineering Platforms'),
    ('devops_infra', 'DevOps & Cloud Infrastructure'),
    ('cybersecurity', 'Information Security & Cryptography'),
    ('enterprise_saas', 'Enterprise Software & Collaboration'),
    ('cleantech_climate', 'Clean Energy & Climate Technology'),
    ('ecommerce_retail', 'Commerce Platforms & Logistics'),
    ('gaming_entertainment', 'Interactive Media & Audio'),
    ('aerospace_defense', 'Aerospace, Defense & SpaceTech'),
    ('hardware_iot', 'Hardware, Semiconductors & Robotics'),
    ('proptech', 'Real Estate & Property Technology'),
    ('edtech', 'Educational Technology & Learning'),
    ('legaltech', 'Legal Intelligence & Compliance')
ON CONFLICT (code) DO NOTHING;


-- =============================================================================
-- SECTION 3: CORE APPLICATION ENTITIES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: user_profile
-- Description: Candidate profile, target roles, experience tier, and career settings.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    visa_status VARCHAR(100) NOT NULL DEFAULT 'None',
    remote_preference VARCHAR(50) NOT NULL DEFAULT 'Remote',
    tone_directives JSON NOT NULL DEFAULT '{}'::json,
    target_roles JSON NOT NULL DEFAULT '[]'::json,
    target_locations JSON NOT NULL DEFAULT '[]'::json,
    headline VARCHAR(255) NULL,
    target_role VARCHAR(255) NULL,
    target_location VARCHAR(255) NULL,
    years_experience INTEGER NOT NULL DEFAULT 0,
    skills JSON NOT NULL DEFAULT '[]'::json,
    preferences JSON NOT NULL DEFAULT '{}'::json,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_profile_email ON user_profile (email);

-- -----------------------------------------------------------------------------
-- Table: cv_block
-- Description: Semantic career accomplishment and skill blocks with 1536-dim vector embeddings.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cv_block (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE RESTRICT,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metrics JSON NOT NULL DEFAULT '{}'::json,
    skills JSON NOT NULL DEFAULT '[]'::json,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_cv_block_user_profile_id ON cv_block (user_profile_id);
CREATE INDEX IF NOT EXISTS ix_cv_block_category ON cv_block (category);
CREATE INDEX IF NOT EXISTS idx_cv_block_embedding_hnsw ON cv_block USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- -----------------------------------------------------------------------------
-- Table: company_dossier
-- Description: Architectural & business intelligence on employers (tech stack, news, culture).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_dossier (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    canonical_name VARCHAR(255) NOT NULL DEFAULT '',
    domain VARCHAR(255) NULL,
    aliases JSON NOT NULL DEFAULT '[]'::json,
    industry VARCHAR(100) NULL REFERENCES industry_sector(code) ON DELETE RESTRICT,
    tech_stack JSON NOT NULL DEFAULT '[]'::json,
    recent_news JSON NOT NULL DEFAULT '[]'::json,
    business_model TEXT NULL,
    culture_notes TEXT NULL,
    data_origin VARCHAR(50) NOT NULL DEFAULT 'live',
    schema_version VARCHAR(50) NOT NULL DEFAULT 'v2',
    field_provenance JSON NOT NULL DEFAULT '{}'::json,
    last_fetched_at TIMESTAMPTZ NULL,
    next_refresh_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_company_dossier_company_name ON company_dossier (company_name);
CREATE INDEX IF NOT EXISTS ix_company_dossier_canonical_name ON company_dossier (canonical_name);
CREATE INDEX IF NOT EXISTS ix_company_dossier_domain ON company_dossier (domain);
CREATE INDEX IF NOT EXISTS ix_company_dossier_industry ON company_dossier (industry);
CREATE INDEX IF NOT EXISTS ix_company_dossier_next_refresh_at ON company_dossier (next_refresh_at);

-- -----------------------------------------------------------------------------
-- Table: ats_board
-- Description: Registered career boards monitored by the autonomous crawler.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ats_board (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL REFERENCES ats_provider(code) ON DELETE RESTRICT,
    slug VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NULL,
    industry VARCHAR(100) NULL REFERENCES industry_sector(code) ON DELETE RESTRICT,
    company_dossier_id UUID NULL REFERENCES company_dossier(id) ON DELETE RESTRICT,
    headquarters_country VARCHAR(100) NULL,
    headquarters_country_code VARCHAR(10) NULL,
    primary_region VARCHAR(50) NULL,
    tier INTEGER NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ NULL,
    next_sync_at TIMESTAMPTZ NULL,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    discovered_via VARCHAR(50) NOT NULL DEFAULT 'seed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ats_board_provider_slug UNIQUE (provider, slug)
);

CREATE INDEX IF NOT EXISTS ix_ats_board_provider ON ats_board (provider);
CREATE INDEX IF NOT EXISTS ix_ats_board_slug ON ats_board (slug);
CREATE INDEX IF NOT EXISTS ix_ats_board_company_name ON ats_board (company_name);
CREATE INDEX IF NOT EXISTS ix_ats_board_industry ON ats_board (industry);
CREATE INDEX IF NOT EXISTS ix_ats_board_headquarters_country_code ON ats_board (headquarters_country_code);
CREATE INDEX IF NOT EXISTS ix_ats_board_next_sync_at ON ats_board (next_sync_at);

-- -----------------------------------------------------------------------------
-- Table: job_listing
-- Description: Discovered job listings with decoupled modality, geography, and visa parsing.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_listing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    url VARCHAR(1024) NULL,
    apply_url VARCHAR(1024) NULL,
    ats_board_id UUID NOT NULL REFERENCES ats_board(id) ON DELETE RESTRICT,
    ats_provider VARCHAR(50) NOT NULL REFERENCES ats_provider(code) ON DELETE RESTRICT,
    ats_board_slug VARCHAR(255) NOT NULL,
    source_job_id VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL REFERENCES industry_sector(code) ON DELETE RESTRICT,
    company_dossier_id UUID NULL REFERENCES company_dossier(id) ON DELETE RESTRICT,
    raw_location VARCHAR(500) NOT NULL DEFAULT 'Remote',
    city VARCHAR(255) NULL,
    state_province VARCHAR(255) NULL,
    state_province_code VARCHAR(50) NULL,
    country VARCHAR(100) NULL,
    country_code VARCHAR(10) NULL,
    primary_region VARCHAR(50) NULL,
    workplace_type VARCHAR(50) NOT NULL DEFAULT 'on_site',
    remote_scope VARCHAR(50) NOT NULL DEFAULT 'none',
    salary_range VARCHAR(100) NULL,
    raw_description TEXT NOT NULL,
    ats_requirements JSON NOT NULL DEFAULT '{}'::json,
    visa_sponsorship VARCHAR(50) NULL,
    visa_notes TEXT NULL,
    visa_types JSON NOT NULL DEFAULT '[]'::json,
    fingerprint VARCHAR(64) NULL,
    content_hash VARCHAR(64) NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    data_origin VARCHAR(50) NOT NULL DEFAULT 'live',
    source_confidence VARCHAR(50) NOT NULL DEFAULT 'high',
    verification JSON NOT NULL DEFAULT '{}'::json,
    extraction_version VARCHAR(50) NOT NULL DEFAULT 'v2',
    posted_at TIMESTAMPTZ NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_fetched_at TIMESTAMPTZ NULL,
    last_verified_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_job_listing_provider_slug_jobid UNIQUE (ats_provider, ats_board_slug, source_job_id)
);

CREATE INDEX IF NOT EXISTS ix_job_listing_ats_board_id ON job_listing (ats_board_id);
CREATE INDEX IF NOT EXISTS ix_job_listing_ats_provider ON job_listing (ats_provider);
CREATE INDEX IF NOT EXISTS ix_job_listing_ats_board_slug ON job_listing (ats_board_slug);
CREATE INDEX IF NOT EXISTS ix_job_listing_source_job_id ON job_listing (source_job_id);
CREATE INDEX IF NOT EXISTS ix_job_listing_company_name ON job_listing (company_name);
CREATE INDEX IF NOT EXISTS ix_job_listing_title ON job_listing (title);
CREATE INDEX IF NOT EXISTS ix_job_listing_industry ON job_listing (industry);
CREATE INDEX IF NOT EXISTS ix_job_listing_city ON job_listing (city);
CREATE INDEX IF NOT EXISTS ix_job_listing_state_province_code ON job_listing (state_province_code);
CREATE INDEX IF NOT EXISTS ix_job_listing_country_code ON job_listing (country_code);
CREATE INDEX IF NOT EXISTS ix_job_listing_workplace_type ON job_listing (workplace_type);
CREATE INDEX IF NOT EXISTS ix_job_listing_remote_scope ON job_listing (remote_scope);
CREATE INDEX IF NOT EXISTS ix_job_listing_visa_sponsorship ON job_listing (visa_sponsorship);
CREATE INDEX IF NOT EXISTS ix_job_listing_status ON job_listing (status);
CREATE INDEX IF NOT EXISTS ix_job_listing_fingerprint ON job_listing (fingerprint);

-- -----------------------------------------------------------------------------
-- Table: application
-- Description: User job application tracking, status stages, and candidate notes.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS application (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE RESTRICT,
    job_listing_id UUID NOT NULL REFERENCES job_listing(id) ON DELETE RESTRICT,
    status VARCHAR(50) NOT NULL DEFAULT 'saved',
    notes TEXT NULL,
    custom_metadata JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_application_user_job UNIQUE (user_profile_id, job_listing_id)
);

CREATE INDEX IF NOT EXISTS ix_application_user_profile_id ON application (user_profile_id);
CREATE INDEX IF NOT EXISTS ix_application_job_listing_id ON application (job_listing_id);
CREATE INDEX IF NOT EXISTS ix_application_status ON application (status);

-- -----------------------------------------------------------------------------
-- Table: feedback_log
-- Description: Candidate interview & CV tailoring feedback for recursive prompt optimization.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_profile_id UUID NULL REFERENCES user_profile(id) ON DELETE RESTRICT,
    thread_id VARCHAR(255) NOT NULL,
    user_feedback TEXT NOT NULL,
    prompt_weight_adjustments JSON NOT NULL DEFAULT '{}'::json,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_feedback_log_user_profile_id ON feedback_log (user_profile_id);
CREATE INDEX IF NOT EXISTS ix_feedback_log_thread_id ON feedback_log (thread_id);


-- =============================================================================
-- SECTION 4: INGESTION PIPELINE & WORKER OPERATIONAL TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: ingestion_run
-- Description: Telemetry and run metrics for board sync execution.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingestion_run (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ats_board_id UUID NOT NULL REFERENCES ats_board(id) ON DELETE RESTRICT,
    ats_provider VARCHAR(50) NOT NULL REFERENCES ats_provider(code) ON DELETE RESTRICT,
    board_slug VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    new_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    closed_count INTEGER NOT NULL DEFAULT 0,
    rejected_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ingestion_run_ats_board_id ON ingestion_run (ats_board_id);
CREATE INDEX IF NOT EXISTS ix_ingestion_run_ats_provider ON ingestion_run (ats_provider);
CREATE INDEX IF NOT EXISTS ix_ingestion_run_board_slug ON ingestion_run (board_slug);

-- -----------------------------------------------------------------------------
-- Table: ingestion_task
-- Description: Asynchronous queue for heavy extraction workers (SELECT FOR UPDATE SKIP LOCKED).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingestion_task (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(50) NOT NULL,
    dedupe_key VARCHAR(255) NOT NULL,
    ats_board_id UUID NULL REFERENCES ats_board(id) ON DELETE RESTRICT,
    ats_provider VARCHAR(50) NULL REFERENCES ats_provider(code) ON DELETE RESTRICT,
    board_slug VARCHAR(255) NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5,
    payload JSON NOT NULL DEFAULT '{}'::json,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    error_message TEXT NULL,
    scheduled_for TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    locked_until TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_ingestion_task_dedupe_key ON ingestion_task (dedupe_key);
CREATE INDEX IF NOT EXISTS ix_ingestion_task_task_type ON ingestion_task (task_type);
CREATE INDEX IF NOT EXISTS ix_ingestion_task_status ON ingestion_task (status);
CREATE INDEX IF NOT EXISTS ix_ingestion_task_priority ON ingestion_task (priority);
CREATE INDEX IF NOT EXISTS ix_ingestion_task_scheduled_for ON ingestion_task (scheduled_for);
CREATE INDEX IF NOT EXISTS ix_ingestion_task_locked_until ON ingestion_task (locked_until);
CREATE INDEX IF NOT EXISTS ix_ingestion_task_ats_board_id ON ingestion_task (ats_board_id);

-- -----------------------------------------------------------------------------
-- Table: provider_usage
-- Description: Upstream API call quotas and rate limit accounting per period.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL REFERENCES ats_provider(code) ON DELETE RESTRICT,
    period_key VARCHAR(50) NOT NULL,
    call_count INTEGER NOT NULL DEFAULT 0,
    token_count INTEGER NOT NULL DEFAULT 0,
    max_calls INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_provider_usage_period UNIQUE (provider, period_key)
);

CREATE INDEX IF NOT EXISTS ix_provider_usage_provider ON provider_usage (provider);
CREATE INDEX IF NOT EXISTS ix_provider_usage_period_key ON provider_usage (period_key);

-- -----------------------------------------------------------------------------
-- Table: provider_state
-- Description: Circuit breaker status, error counters, and cooldown tracking for ATS providers.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL REFERENCES ats_provider(code) ON DELETE RESTRICT,
    is_circuit_open BOOLEAN NOT NULL DEFAULT FALSE,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_failure_at TIMESTAMPTZ NULL,
    cooldown_until TIMESTAMPTZ NULL,
    last_error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_provider_state_provider ON provider_state (provider);


-- =============================================================================
-- SECTION 6: CANDIDATE ACCOUNTS, MULTI-PERSONA MODELING & MATCH CACHE (ADR-007 / ADR-008)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: user_account
-- Description: Central authentication identity, work authorization, and master career profile.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NULL,
    full_name VARCHAR(255) NOT NULL,
    visa_status VARCHAR(100) NOT NULL DEFAULT 'None',
    citizenship_country_code VARCHAR(10) NULL,
    preferred_locations JSON NOT NULL DEFAULT '[]'::json,
    remote_preference VARCHAR(50) NOT NULL DEFAULT 'Remote',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_account_email ON user_account (email);
CREATE INDEX IF NOT EXISTS ix_user_account_visa_status ON user_account (visa_status);

-- -----------------------------------------------------------------------------
-- Table: candidate_persona
-- Description: Multi-persona career tracks (e.g. Universal Profile, AI Engineer, Java Backend).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS candidate_persona (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_account_id UUID NOT NULL REFERENCES user_account(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,
    is_common_persona BOOLEAN NOT NULL DEFAULT FALSE,
    headline VARCHAR(255) NULL,
    target_roles JSON NOT NULL DEFAULT '[]'::json,
    target_industries JSON NOT NULL DEFAULT '[]'::json,
    years_experience INTEGER NOT NULL DEFAULT 0,
    seniority_level VARCHAR(50) NOT NULL DEFAULT 'mid',
    min_salary INTEGER NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_candidate_persona_user_account_id ON candidate_persona (user_account_id);
CREATE INDEX IF NOT EXISTS ix_candidate_persona_is_common ON candidate_persona (is_common_persona);

-- -----------------------------------------------------------------------------
-- Table: persona_skill
-- Description: Normalized skills matrix per candidate persona with proficiency tiers.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS persona_skill (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES candidate_persona(id) ON DELETE RESTRICT,
    skill_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'tool',
    proficiency VARCHAR(50) NOT NULL DEFAULT 'intermediate',
    years_experience INTEGER NOT NULL DEFAULT 1,
    is_core BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_persona_skill_unique UNIQUE (persona_id, skill_name)
);

CREATE INDEX IF NOT EXISTS ix_persona_skill_persona_id ON persona_skill (persona_id);
CREATE INDEX IF NOT EXISTS ix_persona_skill_skill_name ON persona_skill (skill_name);

-- -----------------------------------------------------------------------------
-- Table: persona_cv_block_rel
-- Description: Junction table mapping master cv_blocks to specific candidate personas.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS persona_cv_block_rel (
    persona_id UUID NOT NULL REFERENCES candidate_persona(id) ON DELETE RESTRICT,
    cv_block_id UUID NOT NULL REFERENCES cv_block(id) ON DELETE RESTRICT,
    priority_weight FLOAT NOT NULL DEFAULT 1.0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (persona_id, cv_block_id)
);

CREATE INDEX IF NOT EXISTS ix_persona_cv_block_rel_block ON persona_cv_block_rel (cv_block_id);

-- -----------------------------------------------------------------------------
-- Table: job_match_cache
-- Description: Cached multi-factor match probability and diagnostics per persona-job pair.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_match_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES candidate_persona(id) ON DELETE RESTRICT,
    job_listing_id UUID NOT NULL REFERENCES job_listing(id) ON DELETE RESTRICT,
    match_score FLOAT NOT NULL DEFAULT 0.0,
    hard_gate_pass BOOLEAN NOT NULL DEFAULT TRUE,
    skill_overlap_score FLOAT NOT NULL DEFAULT 0.0,
    semantic_score FLOAT NOT NULL DEFAULT 0.0,
    seniority_score FLOAT NOT NULL DEFAULT 0.0,
    prestige_booster FLOAT NOT NULL DEFAULT 0.0,
    achievement_booster FLOAT NOT NULL DEFAULT 0.0,
    missing_skills JSON NOT NULL DEFAULT '[]'::json,
    matched_skills JSON NOT NULL DEFAULT '[]'::json,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_persona_job_match UNIQUE (persona_id, job_listing_id)
);

CREATE INDEX IF NOT EXISTS ix_job_match_cache_persona_score ON job_match_cache (persona_id, match_score DESC);
CREATE INDEX IF NOT EXISTS ix_job_match_cache_job_listing_id ON job_match_cache (job_listing_id);

-- Link user_profile and cv_block to user_account
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS visa_status VARCHAR(100) NOT NULL DEFAULT 'None';
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS remote_preference VARCHAR(50) NOT NULL DEFAULT 'Remote';
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS tone_directives JSON NOT NULL DEFAULT '{}'::json;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS target_roles JSON NOT NULL DEFAULT '[]'::json;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS target_locations JSON NOT NULL DEFAULT '[]'::json;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS user_account_id UUID NULL REFERENCES user_account(id) ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS ix_user_profile_user_account_id ON user_profile (user_account_id);

ALTER TABLE cv_block ADD COLUMN IF NOT EXISTS user_account_id UUID NULL REFERENCES user_account(id) ON DELETE RESTRICT;
CREATE INDEX IF NOT EXISTS ix_cv_block_user_account_id ON cv_block (user_account_id);
ALTER TABLE cv_block ALTER COLUMN user_profile_id DROP NOT NULL;
ALTER TABLE cv_block ALTER COLUMN organization DROP NOT NULL;
ALTER TABLE cv_block ALTER COLUMN embedding DROP NOT NULL;


