-- =============================================================================
-- Career-OS: Domain Alignment & Context Scoring Schema Expansion
-- Migration: 0003_domain_alignment_schema.sql
-- =============================================================================
-- Description:
--   Expands the schema to support Explicit Domain Alignment (S_domain) and
--   Unified Context Blending (S_context):
--   1. Industry vertical classification (industry_vertical) and domain strictness
--      tier (domain_strictness) on job_listing.
--   2. Verified organizational sector tags (industry_tags) on cv_block with GIN index.
--   3. Granular domain_score and context_score diagnostic telemetry on job_match_cache.
-- =============================================================================

-- =============================================================================
-- SECTION 1: JOB LISTING DOMAIN ATTRIBUTES
-- =============================================================================

ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS industry_vertical VARCHAR(64) NULL,
    ADD COLUMN IF NOT EXISTS domain_strictness FLOAT NOT NULL DEFAULT 0.5;

CREATE INDEX IF NOT EXISTS idx_job_listing_industry_vertical
    ON job_listing (industry_vertical);


-- =============================================================================
-- SECTION 2: CV BLOCK INDUSTRY SECTOR TAGS
-- =============================================================================

ALTER TABLE cv_block
    ADD COLUMN IF NOT EXISTS industry_tags JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_cv_block_industry_tags_gin
    ON cv_block USING gin (industry_tags jsonb_path_ops);


-- =============================================================================
-- SECTION 3: JOB MATCH CACHE DOMAIN TELEMETRY
-- =============================================================================

ALTER TABLE job_match_cache
    ADD COLUMN IF NOT EXISTS domain_score FLOAT NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS context_score FLOAT NOT NULL DEFAULT 0.0;
