-- ═══════════════════════════════════════════════════════════════
-- PromptForge v2.0 — Phase 1 Database Migration
-- ═══════════════════════════════════════════════════════════════
-- 
-- Purpose: Add missing columns for RLS (Row Level Security) and clarification loop
-- Run in: Supabase SQL Editor (https://cckznjkzsfypssgecyya.supabase.co)
-- 
-- Tables affected:
--   - conversations (add: user_id, pending_clarification, clarification_key)
--   - prompt_history (add: user_id)
--
-- Safety: All operations use IF NOT EXISTS — safe to run multiple times
-- ═══════════════════════════════════════════════════════════════

-- ── conversations table ────────────────────────────────────────

-- Add user_id for RLS (Row Level Security)
-- This links conversations to authenticated users via JWT
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add clarification loop support columns
-- pending_clarification: True when waiting for user's answer to clarification question
-- clarification_key: Which field is being clarified (e.g., "target_audience")
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS pending_clarification BOOLEAN DEFAULT FALSE;

ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS clarification_key TEXT;

-- Add index for faster clarification flag lookups
CREATE INDEX IF NOT EXISTS idx_conversations_session_clarification 
ON conversations(session_id, pending_clarification) 
WHERE pending_clarification = TRUE;

-- ── prompt_history table ───────────────────────────────────────

-- Add user_id for RLS (Row Level Security)
-- This links prompt history to authenticated users
ALTER TABLE prompt_history 
ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add index for faster user-specific history queries
CREATE INDEX IF NOT EXISTS idx_prompt_history_user_id 
ON prompt_history(user_id, created_at DESC);

-- ── Verification ───────────────────────────────────────────────

-- Show column info for verification
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name IN ('conversations', 'prompt_history')
  AND column_name IN ('user_id', 'pending_clarification', 'clarification_key')
ORDER BY table_name, column_name;

-- ═══════════════════════════════════════════════════════════════
-- Migration Complete
-- ═══════════════════════════════════════════════════════════════
-- 
-- Next steps:
-- 1. Verify columns exist (check query results above)
-- 2. Test API endpoints with JWT authentication
-- 3. Confirm RLS policies are working (user-specific data isolation)
--
-- RLS Policies (if not already created):
--   ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
--   CREATE POLICY "Users can view own conversations" 
--     ON conversations FOR SELECT 
--     USING (auth.uid()::text = user_id::text);
--   CREATE POLICY "Users can insert own conversations" 
--     ON conversations FOR INSERT 
--     WITH CHECK (auth.uid()::text = user_id::text);
-- ═══════════════════════════════════════════════════════════════
