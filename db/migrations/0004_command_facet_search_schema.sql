-- =============================================================================
-- Career-OS: Command-Facet Search Engine, Tokenized Omnibar, and Discovery Schema
-- Migration: 0004_command_facet_search_schema.sql
-- =============================================================================
-- Description:
--   Expands the schema to support the Command-Facet Search Engine:
--   1. Geographic & commute bounds (latitude, longitude, cbsa_metro_code, excluded_states).
--   2. Tri-tier work authorization attributes (is_everify_confirmed, citizenship_restricted, uscis_filings_count).
--   3. Normalized compensation bounds (salary_min_usd, salary_max_usd, prevailing_wage_estimate).
--   4. Spatial and GIN containment indexes.
-- =============================================================================

-- =============================================================================
-- SECTION 1: GEOGRAPHIC, COMMUTE & MODALITY JURISDICTIONS
-- =============================================================================

ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION NULL,
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION NULL,
    ADD COLUMN IF NOT EXISTS cbsa_metro_code VARCHAR(16) NULL,
    ADD COLUMN IF NOT EXISTS excluded_states JSONB NULL;

CREATE INDEX IF NOT EXISTS idx_job_listing_cbsa_metro_code
    ON job_listing (cbsa_metro_code);

CREATE INDEX IF NOT EXISTS idx_job_listing_lat_lon
    ON job_listing (latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_job_listing_excluded_states_gin
    ON job_listing USING gin (excluded_states jsonb_path_ops);


-- =============================================================================
-- SECTION 2: WORK AUTHORIZATION & IMMIGRATION FILINGS
-- =============================================================================

ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS is_everify_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS citizenship_restricted BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS uscis_filings_count INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_job_listing_is_everify
    ON job_listing (is_everify_confirmed);

CREATE INDEX IF NOT EXISTS idx_job_listing_citizenship_restricted
    ON job_listing (citizenship_restricted);


-- =============================================================================
-- SECTION 3: NORMALIZED USD COMPENSATION BOUNDS
-- =============================================================================

ALTER TABLE job_listing
    ADD COLUMN IF NOT EXISTS salary_min_usd INTEGER NULL,
    ADD COLUMN IF NOT EXISTS salary_max_usd INTEGER NULL,
    ADD COLUMN IF NOT EXISTS prevailing_wage_estimate INTEGER NULL;

CREATE INDEX IF NOT EXISTS idx_job_listing_salary_bounds
    ON job_listing (salary_min_usd, salary_max_usd);

