-- Migration 027: Add missing columns to user_profiles
-- Date: 2026-04-06
-- Purpose: Backend writes these columns but they don't exist in schema.
-- Without this, profile save silently drops all user data.

ALTER TABLE public.user_profiles
  ADD COLUMN IF NOT EXISTS bio            TEXT,
  ADD COLUMN IF NOT EXISTS location       VARCHAR(100),
  ADD COLUMN IF NOT EXISTS job_title      VARCHAR(100),
  ADD COLUMN IF NOT EXISTS company        VARCHAR(100),
  ADD COLUMN IF NOT EXISTS website        VARCHAR(200),
  ADD COLUMN IF NOT EXISTS github         VARCHAR(100),
  ADD COLUMN IF NOT EXISTS twitter        VARCHAR(100),
  ADD COLUMN IF NOT EXISTS linkedin       VARCHAR(200),
  ADD COLUMN IF NOT EXISTS avatar_url     VARCHAR(500),
  ADD COLUMN IF NOT EXISTS phone          VARCHAR(20),
  ADD COLUMN IF NOT EXISTS xp_total       INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS loyalty_tier   VARCHAR(20) DEFAULT 'Bronze';

-- Verify
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'user_profiles'
  AND column_name IN ('bio', 'location', 'job_title', 'company', 'website',
                       'github', 'twitter', 'linkedin', 'avatar_url', 'phone',
                       'xp_total', 'loyalty_tier')
ORDER BY ordinal_position;
