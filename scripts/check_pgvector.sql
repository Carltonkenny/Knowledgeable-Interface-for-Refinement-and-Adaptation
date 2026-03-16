-- Check if pgvector is installed in your Supabase database
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/_/sql

-- Check 1: Is vector extension available?
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check 2: Can we create vector type?
-- (Don't worry, this is safe - just checking)
SELECT pg_typeof('[1,2,3]'::vector);

-- Check 3: List all tables with vector columns
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE data_type = 'USER-DEFINED' 
  AND udt_name = 'vector';
