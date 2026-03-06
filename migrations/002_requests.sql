-- =====================================================
-- Migration 002: requests table — add columns + RLS
-- =====================================================
-- Purpose: Add user_id for RLS, quality tracking fields
-- Run in: Supabase SQL Editor (after 001)
-- =====================================================

-- ── Add new columns ─────────────────────────────

ALTER TABLE requests
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS prompt_diff JSONB,
    ADD COLUMN IF NOT EXISTS quality_score JSONB,
    ADD COLUMN IF NOT EXISTS agents_used TEXT[],
    ADD COLUMN IF NOT EXISTS agents_skipped TEXT[],
    ADD COLUMN IF NOT EXISTS user_rating INT,
    ADD COLUMN IF NOT EXISTS input_modality TEXT;

-- ── Index for fast lookups ──────────────────────

CREATE INDEX IF NOT EXISTS idx_requests_user_id 
    ON requests(user_id);

CREATE INDEX IF NOT EXISTS idx_requests_session_id 
    ON requests(session_id);

-- ── Enable Row Level Security ───────────────────

ALTER TABLE requests ENABLE ROW LEVEL SECURITY;

-- ── RLS Policies ────────────────────────────────
-- Users can ONLY see/edit their own requests

CREATE POLICY IF NOT EXISTS "users_select_own_requests" ON requests
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_insert_own_requests" ON requests
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- Migration 002 complete
-- =====================================================
