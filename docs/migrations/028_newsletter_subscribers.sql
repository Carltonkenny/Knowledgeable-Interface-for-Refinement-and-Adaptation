-- Migration 028: Newsletter Subscribers Table
-- Stores email subscribers from footer newsletter signup
-- Connected to Supabase — no third-party service needed

CREATE TABLE IF NOT EXISTS newsletter_subscribers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  subscribed_at TIMESTAMPTZ DEFAULT now(),
  source TEXT DEFAULT 'footer',
  is_active BOOLEAN DEFAULT true
);

-- RLS: service role can read all, anyone can insert
ALTER TABLE newsletter_subscribers ENABLE ROW LEVEL SECURITY;

-- Allow anyone to subscribe (insert only)
CREATE POLICY "Anyone can subscribe"
  ON newsletter_subscribers
  FOR INSERT
  WITH CHECK (true);

-- Only service role can read/update/delete
-- (handled by default RLS — no policy = no access for anon)

-- Index on email for fast duplicate checks
CREATE INDEX IF NOT EXISTS idx_newsletter_email
  ON newsletter_subscribers (email);

-- Index on subscribed_at for analytics
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribed_at
  ON newsletter_subscribers (subscribed_at DESC);
