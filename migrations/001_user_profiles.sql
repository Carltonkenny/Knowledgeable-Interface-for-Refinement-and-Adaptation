-- =====================================================
-- Migration 001: user_profiles table
-- =====================================================
-- Purpose: Core table for user personalization (the "moat")
-- Run in: Supabase SQL Editor
-- URL: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
-- =====================================================

-- ── Create user_profiles table ──────────────────

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    
    -- Core fields from RULES.md
    dominant_domains TEXT[],              -- Top 3 domains user works in
    prompt_quality_trend TEXT,            -- "improving" | "stable" | "declining"
    avg_prompt_length INT,                -- Moving average of prompt length
    clarification_rate FLOAT,             -- 0.0-1.0 (how often needs clarification)
    preferred_tone TEXT,                  -- "casual" | "formal" | "technical"
    notable_patterns TEXT[],              -- ["likes_detailed_steps", "prefers_examples"]
    personality_adaptation JSONB,         -- Kira's tone adjustments per domain
    total_sessions INT DEFAULT 0,         -- Total conversations
    mcp_trust_level INT DEFAULT 0,        -- 0 | 1 | 2
    input_modality_trend TEXT,            -- "text" | "voice" | "mixed"
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes for fast lookups ────────────────────

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id 
    ON user_profiles(user_id);

-- ── Enable Row Level Security ───────────────────

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- ── RLS Policies ────────────────────────────────
-- Users can ONLY see/edit their own profile

CREATE POLICY "users_select_own_profile" ON user_profiles
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_insert_own_profile" ON user_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users_update_own_profile" ON user_profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "users_delete_own_profile" ON user_profiles
    FOR DELETE
    USING (auth.uid() = user_id);

-- ── Trigger to update updated_at ────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Migration 001 complete
-- =====================================================
