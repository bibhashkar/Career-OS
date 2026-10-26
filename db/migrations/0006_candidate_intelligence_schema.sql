-- Migration: 0006_candidate_intelligence_schema.sql
-- Description: Adds structured career_intelligence JSONB column to candidate_persona
--              to persist education (degree, major, university tier), per-role tenures,
--              projects, hackathons/competitions, awards, and external links.

-- 1. Extend candidate_persona with career_intelligence JSONB
ALTER TABLE candidate_persona
    ADD COLUMN IF NOT EXISTS career_intelligence JSONB NOT NULL DEFAULT '{}'::jsonb;

-- 2. GIN index for fast JSONB querying on career_intelligence
CREATE INDEX IF NOT EXISTS idx_candidate_persona_career_intelligence_gin
    ON candidate_persona USING gin (career_intelligence jsonb_path_ops);

