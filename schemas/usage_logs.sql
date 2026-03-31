-- ═══ USAGE LOGS TABLE (Rate Limiting Support) ═══════════════════
-- Tracks user requests per day/month for usage-based limits
-- Used by: /usage/current, /usage/history endpoints

-- Create usage_logs table
CREATE TABLE IF NOT EXISTS usage_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  date date NOT NULL,
  month integer NOT NULL,
  year integer NOT NULL,
  requests_count integer DEFAULT 1,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id, date)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_date ON usage_logs(user_id, date);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_month ON usage_logs(user_id, month, year);
CREATE INDEX IF NOT EXISTS idx_usage_logs_date ON usage_logs(date);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_usage_logs_updated_at
  BEFORE UPDATE ON usage_logs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only view/insert their own usage logs
CREATE POLICY "Users can view their own usage logs"
  ON usage_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own usage logs"
  ON usage_logs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own usage logs"
  ON usage_logs FOR UPDATE
  USING (auth.uid() = user_id);

-- Service role can manage all usage logs (for background tasks)
CREATE POLICY "Service role can manage all usage logs"
  ON usage_logs FOR ALL
  USING (auth.jwt()->>'role' = 'service_role');

-- Add table comment
COMMENT ON TABLE usage_logs IS 
  'Tracks user API request usage for rate limiting and analytics. Stores daily and monthly request counts per user.';

-- Add column comments
COMMENT ON COLUMN usage_logs.user_id IS 'User UUID from auth.users';
COMMENT ON COLUMN usage_logs.date IS 'Calendar date (UTC) for daily aggregation';
COMMENT ON COLUMN usage_logs.month IS 'Month (1-12) for monthly aggregation';
COMMENT ON COLUMN usage_logs.year IS 'Year for monthly aggregation';
COMMENT ON COLUMN usage_logs.requests_count IS 'Number of requests made on this date';
