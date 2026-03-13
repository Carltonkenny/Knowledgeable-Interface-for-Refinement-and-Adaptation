-- migrations/016_add_prompt_feedback.sql
-- Track implicit feedback from user behavior (copy, edit, save)
-- RULES.md: RLS enabled, indexed for performance, silent fail safe

-- Create feedback table
CREATE TABLE IF NOT EXISTS prompt_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,  -- copy|edit|save
    edit_distance FLOAT,          -- For edit feedback (0.0-1.0)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for fast queries (RULES.md Performance Rule #3)
CREATE INDEX IF NOT EXISTS idx_feedback_user ON prompt_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session ON prompt_feedback(session_id, prompt_id);
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON prompt_feedback(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON prompt_feedback(feedback_type);

-- RLS Policies (RULES.md Security Rule #7)
ALTER TABLE prompt_feedback ENABLE ROW LEVEL SECURITY;

-- Users can only insert their own feedback
CREATE POLICY "Users can insert own feedback"
    ON prompt_feedback
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can view their own feedback (for analytics)
CREATE POLICY "Users can view own feedback"
    ON prompt_feedback
    FOR SELECT
    USING (auth.uid() = user_id);

-- Service role has full access (for background tasks)
CREATE POLICY "Service role full access"
    ON prompt_feedback
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Comment documenting purpose (RULES.md Documentation Rule #2)
COMMENT ON TABLE prompt_feedback IS 
    'Implicit feedback signals from user behavior (copy, edit, save). Used for continuous quality learning.';

COMMENT ON COLUMN prompt_feedback.feedback_type IS 
    'Type of feedback: copy (user copied prompt), edit (user modified before copying), save (user saved to library)';

COMMENT ON COLUMN prompt_feedback.edit_distance IS 
    'Levenshtein distance ratio (0.0-1.0) for edit feedback. Higher = more changes made by user.';
