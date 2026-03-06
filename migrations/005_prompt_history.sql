-- =====================================================
-- Migration 005: prompt_history table — add user_id + RLS
-- =====================================================
-- Purpose: Add user_id for RLS (required for /history endpoint)
-- Run in: Supabase SQL Editor (after 001-004)
-- =====================================================

-- ── Add new column ──────────────────────────────

ALTER TABLE prompt_history
    ADD COLUMN IF NOT EXISTS user_id UUID;

-- ── Index for fast lookups ──────────────────────

CREATE INDEX IF NOT EXISTS idx_prompt_history_user_id 
    ON prompt_history(user_id);

CREATE INDEX IF NOT EXISTS idx_prompt_history_session_id 
    ON prompt_history(session_id);

-- ── Enable Row Level Security ───────────────────

ALTER TABLE prompt_history ENABLE ROW LEVEL SECURITY;

-- ── RLS Policies ────────────────────────────────
-- Users can ONLY see/edit their own history

CREATE POLICY IF NOT EXISTS "users_select_own_history" ON prompt_history
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_insert_own_history" ON prompt_history
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- Migration 005 complete
-- =====================================================
