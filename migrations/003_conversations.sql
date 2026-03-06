-- =====================================================
-- Migration 003: conversations table — add columns + RLS
-- =====================================================
-- Purpose: Add user_id for RLS, clarification loop fields
-- Run in: Supabase SQL Editor (after 001, 002)
-- =====================================================

-- ── Add new columns ─────────────────────────────

ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS user_id UUID,
    ADD COLUMN IF NOT EXISTS kira_tone_used TEXT,
    ADD COLUMN IF NOT EXISTS pending_clarification BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS clarification_key TEXT;

-- ── Indexes for fast lookups ────────────────────

CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
    ON conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
    ON conversations(session_id);

-- ── Enable Row Level Security ───────────────────

ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- ── RLS Policies ────────────────────────────────
-- Users can ONLY see/edit their own conversations

CREATE POLICY IF NOT EXISTS "users_select_own_conversations" ON conversations
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "users_insert_own_conversations" ON conversations
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- =====================================================
-- Migration 003 complete
-- =====================================================
