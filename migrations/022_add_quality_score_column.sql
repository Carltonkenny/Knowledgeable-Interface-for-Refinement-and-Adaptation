-- Migration 022: Add prompt_quality_score to user_profiles
-- 
-- Purpose: Store user's average prompt quality score for tracking improvement over time
-- Issue: Code in api.py (_adjust_user_quality_score) reads/writes this column but it doesn't exist
-- Impact: All quality score adjustments silently fail (always returns default 0.5)
--
-- Date: 2026-03-16
-- Author: PromptForge v2.0 Fix Session 1

-- Add column
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS prompt_quality_score NUMERIC DEFAULT 0.5;

-- Add index for fast queries on quality trend endpoint
CREATE INDEX IF NOT EXISTS idx_user_profiles_quality_score 
ON user_profiles(user_id, prompt_quality_score);

-- Add comment for future developers
COMMENT ON COLUMN user_profiles.prompt_quality_score IS 
'User average prompt quality score (0.0-1.0). Updated after each prompt engineering session.';

-- Verify column exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'prompt_quality_score'
    ) THEN
        RAISE EXCEPTION 'Migration 022 failed: prompt_quality_score column not created';
    END IF;
END $$;
