-- Migration 029: Add profile analysis columns to user_profiles
-- Date: 2026-04-07
-- Purpose: profile_updater.py writes these columns but they don't exist in schema.
-- Without this, Kira's personalization system silently fails — every profile update
-- is dropped by Supabase with no error logged.
--
-- Written by: profile_updater.py writes these at lines 140-160:
--   - dominant_domains (JSONB array)
--   - prompt_quality_trend (TEXT: 'improving'/'declining'/'stable')
--   - clarification_rate (FLOAT: 0.0-1.0)
--   - notable_patterns (JSONB array)
--   - domain_confidence (FLOAT: 0.0-1.0)
--   - last_profile_sync (TIMESTAMPTZ)

ALTER TABLE public.user_profiles
  ADD COLUMN IF NOT EXISTS dominant_domains     JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS prompt_quality_trend TEXT DEFAULT 'stable',
  ADD COLUMN IF NOT EXISTS clarification_rate   REAL DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS notable_patterns     JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS domain_confidence    REAL DEFAULT 0.5,
  ADD COLUMN IF NOT EXISTS last_profile_sync    TIMESTAMPTZ;

-- Verify
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'user_profiles'
  AND column_name IN (
    'dominant_domains', 'prompt_quality_trend', 'clarification_rate',
    'notable_patterns', 'domain_confidence', 'last_profile_sync'
  )
ORDER BY ordinal_position;

-- Expected output:
-- column_name          | data_type | column_default
-- ---------------------+-----------+----------------
-- dominant_domains     | jsonb     | '[]'::jsonb
-- prompt_quality_trend | text      | 'stable'
-- clarification_rate   | real      | 0
-- notable_patterns     | jsonb     | '[]'::jsonb
-- domain_confidence    | real      | 0.5
-- last_profile_sync    | timestamp | (null)
