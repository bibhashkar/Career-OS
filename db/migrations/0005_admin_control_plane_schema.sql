-- Migration: 0005_admin_control_plane_schema.sql
-- Description: Adds role and last_login_at to user_account, enhances provider_usage with token/cost tracking,
--              and creates the llm_usage_event table for granular AI cost attribution.

-- 1. Extend user_account with role and last_login_at
ALTER TABLE user_account 
    ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'candidate',
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ NULL;

CREATE INDEX IF NOT EXISTS idx_user_account_role ON user_account(role);

-- 2. Extend provider_usage with token breakdown and USD cost tracking
ALTER TABLE provider_usage
    ADD COLUMN IF NOT EXISTS input_tokens INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS output_tokens INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS estimated_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0;

-- 3. Create llm_usage_event table for granular trace-level AI cost attribution
CREATE TABLE IF NOT EXISTS llm_usage_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_account_id UUID NULL REFERENCES user_account(id) ON DELETE SET NULL,
    feature VARCHAR(100) NOT NULL, -- 'cv_tailor', 'ats_grader', 'interview', 'jd_extractor', 'embeddings'
    provider VARCHAR(50) NOT NULL, -- 'gemini', 'openai', 'anthropic'
    model_name VARCHAR(100) NOT NULL, -- 'gemini-2.5-flash', 'gpt-4o', etc.
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'success', -- 'success', 'error', 'timeout'
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_event_feature ON llm_usage_event(feature);
CREATE INDEX IF NOT EXISTS idx_llm_usage_event_provider ON llm_usage_event(provider);
CREATE INDEX IF NOT EXISTS idx_llm_usage_event_created_at ON llm_usage_event(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_event_user ON llm_usage_event(user_account_id);
