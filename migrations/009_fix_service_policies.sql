-- ============================================================
-- Fix: Add service_full_access policies for new tables
-- ============================================================
-- Run in: https://supabase.com/dashboard/project/cckznjkzsfypssgecyya/sql/new
-- ============================================================

-- Add service policy for user_profiles
DROP POLICY IF EXISTS "service_full_access" ON user_profiles;
CREATE POLICY "service_full_access" ON user_profiles
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Add service policy for langmem_memories
DROP POLICY IF EXISTS "service_full_access" ON langmem_memories;
CREATE POLICY "service_full_access" ON langmem_memories
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Verify
SELECT 
  tablename as table_name,
  count(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- Expected: All tables should have 5 policies now
-- ============================================================
