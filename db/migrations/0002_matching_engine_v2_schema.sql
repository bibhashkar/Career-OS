-- =============================================================================
-- Career-OS: Matching Engine v2 Schema Expansion & Indexing
-- Migration: 0002_matching_engine_v2_schema.sql
-- =============================================================================
-- Description:
--   Expands the schema to support the Industrial-Grade Matching Engine v2:
--   1. Normalized compensation ranges (salary_min, salary_max, salary_currency,
--      is_salary_estimated) for S_comp evaluation and DOL/USCIS prevailing wage fallback.
--   2. Cross-ATS deduplication content fingerprinting (content_fingerprint).
--   3. JSONB conversion and GIN inverted indexing for sub-15ms skill requirement filtering.
--   4. Dense 1536-dimensional semantic vector embedding and HNSW indexing on job_listing.
--   5. Granular v2 factor score diagnostics on job_match_cache (d_core, archetype_score,
--      comp_score, freshness_score) with JSONB conversion and GIN indexing.
-- =============================================================================

-- =============================================================================
-- SECTION 1: JOB LISTING SCHEMA EXPANSION
-- =============================================================================

-- 1.1 Normalized Compensation Attributes
ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS salary_min INTEGER NULL,
    ADD COLUMN IF NOT EXISTS salary_max INTEGER NULL,
    ADD COLUMN IF NOT EXISTS salary_currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    ADD COLUMN IF NOT EXISTS is_salary_estimated BOOLEAN NOT NULL DEFAULT FALSE;

-- 1.2 Cross-ATS Deduplication Fingerprint
-- Computes SHA256(company_slug + normalized_title + location_code) across Greenhouse, Lever, Ashby, Workable, SmartRecruiters
ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS content_fingerprint VARCHAR(64) NULL;

-- 1.3 Dense Semantic Vector Embedding (1536-dim)
ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS embedding vector(1536) NULL;

-- 1.4 Convert ats_requirements from JSON to JSONB for Inverted GIN Indexing
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'job_listing'
          AND column_name = 'ats_requirements'
          AND data_type = 'json'
    ) THEN
        ALTER TABLE job_listing
            ALTER COLUMN ats_requirements TYPE JSONB
            USING ats_requirements::jsonb;
    END IF;
END $$;

-- 1.5 B-Tree & Inverted GIN & HNSW Indexes for job_listing
CREATE INDEX IF NOT EXISTS ix_job_listing_content_fingerprint
    ON job_listing (content_fingerprint);

CREATE INDEX IF NOT EXISTS ix_job_listing_salary_range_min_max
    ON job_listing (salary_min, salary_max);

CREATE INDEX IF NOT EXISTS idx_job_listing_ats_requirements_gin
    ON job_listing USING gin (ats_requirements jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_job_listing_embedding_hnsw
    ON job_listing USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);


-- =============================================================================
-- SECTION 2: JOB MATCH CACHE EXPANSION (V2 MULTI-FACTOR TELEMETRY)
-- =============================================================================

-- 2.1 Convert matched_skills and missing_skills to JSONB
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'job_match_cache'
          AND column_name = 'matched_skills'
          AND data_type = 'json'
    ) THEN
        ALTER TABLE job_match_cache
            ALTER COLUMN matched_skills TYPE JSONB
            USING matched_skills::jsonb;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'job_match_cache'
          AND column_name = 'missing_skills'
          AND data_type = 'json'
    ) THEN
        ALTER TABLE job_match_cache
            ALTER COLUMN missing_skills TYPE JSONB
            USING missing_skills::jsonb;
    END IF;
END $$;

-- 2.2 Add v2 Diagnostic Factor Scores
ALTER TABLE job_match_cache
    ADD COLUMN IF NOT EXISTS d_core FLOAT NOT NULL DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS archetype_score FLOAT NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS comp_score FLOAT NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS freshness_score FLOAT NOT NULL DEFAULT 0.0;

-- 2.3 GIN Index for matched_skills
CREATE INDEX IF NOT EXISTS idx_job_match_cache_matched_skills_gin
    ON job_match_cache USING gin (matched_skills jsonb_path_ops);

