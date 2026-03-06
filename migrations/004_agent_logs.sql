-- =====================================================
-- Migration 004: agent_logs table — add columns + RLS
-- =====================================================
-- Purpose: Add user_id for RLS, agent skip tracking
-- Run in: Supabase SQL Editor (after 001-003)
-- =====================================================

-- ── Add new columns ─────────────────────────────

ALTER TABLE agent_logs
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS was_skipped BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS skip_reason TEXT,
    ADD COLUMN IF NOT EXISTS latency_ms INT;

-- ── Index for fast lookups ──────────────────────

CREATE INDEX IF NOT EXISTS idx_agent_logs_user_id 
    ON agent_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_agent_logs_request_id 
    ON agent_logs(request_id);

-- ── Enable Row Level Security ───────────────────

ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- ── RLS Policies ────────────────────────────────
-- Users can ONLY see/edit their own agent logs

CREATE POLICY IF NOT EXISTS "users_select_own_agent_logs" ON agent_logs
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_insert_own_agent_logs" ON agent_logs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- Migration 004 complete
-- =====================================================
