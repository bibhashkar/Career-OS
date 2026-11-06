-- Migration: 0007_provider_usage_relax_fk.sql
-- Description: Drop foreign key constraint on provider_usage(provider) referencing ats_provider(code).
--              provider_usage records usage across all external upstream services (Gemini LLM, DuckDuckGo,
--              GitHub, JobSpy), not just ATS provider platforms.

ALTER TABLE provider_usage
    DROP CONSTRAINT IF EXISTS provider_usage_provider_fkey;
