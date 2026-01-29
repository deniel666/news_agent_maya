-- Migration: Enable Row Level Security on all tables
-- Run this in Supabase SQL Editor after schema.sql
--
-- Security Model:
-- - All tables are accessed via backend service role only
-- - No direct client access (anon key cannot read/write)
-- - Service role bypasses RLS by default in Supabase

-- =============================================================================
-- CREATE MISSING TABLES (if not exist)
-- =============================================================================

-- News sources configuration table
CREATE TABLE IF NOT EXISTS news_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- rss, telegram, twitter
    url VARCHAR(2000),
    category VARCHAR(50),  -- local, business, ai_tech
    reliability_tier VARCHAR(20) DEFAULT 'tier_3',  -- tier_1, tier_2, tier_3
    is_active BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}',  -- Source-specific configuration
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- On-demand job queue table
CREATE TABLE IF NOT EXISTS ondemand_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(500) NOT NULL,
    language_code VARCHAR(10) DEFAULT 'en-SG',
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    priority INTEGER DEFAULT 0,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Add indexes for new tables
CREATE INDEX IF NOT EXISTS idx_news_sources_type ON news_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_news_sources_category ON news_sources(category);
CREATE INDEX IF NOT EXISTS idx_news_sources_active ON news_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_ondemand_jobs_status ON ondemand_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ondemand_jobs_created ON ondemand_jobs(created_at DESC);

-- =============================================================================
-- ENABLE ROW LEVEL SECURITY
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE weekly_briefings ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE ondemand_jobs ENABLE ROW LEVEL SECURITY;

-- Also enable on news_articles if it exists
ALTER TABLE IF EXISTS news_articles ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- CREATE POLICIES
-- =============================================================================
--
-- Policy Strategy:
-- 1. Deny all access to anonymous users (public/anon key)
-- 2. Service role automatically bypasses RLS in Supabase
-- 3. If authenticated users are added later, create specific policies
--
-- Note: In Supabase, when RLS is enabled with no policies, all access is denied
-- except for service_role which bypasses RLS by default.

-- Explicit deny policies for anon role (belt and suspenders)
-- These ensure anon key cannot access anything even if default behavior changes

-- weekly_briefings policies
CREATE POLICY "Deny anon select on weekly_briefings"
    ON weekly_briefings FOR SELECT
    TO anon
    USING (false);

CREATE POLICY "Deny anon insert on weekly_briefings"
    ON weekly_briefings FOR INSERT
    TO anon
    WITH CHECK (false);

CREATE POLICY "Deny anon update on weekly_briefings"
    ON weekly_briefings FOR UPDATE
    TO anon
    USING (false);

CREATE POLICY "Deny anon delete on weekly_briefings"
    ON weekly_briefings FOR DELETE
    TO anon
    USING (false);

-- weekly_videos policies
CREATE POLICY "Deny anon select on weekly_videos"
    ON weekly_videos FOR SELECT
    TO anon
    USING (false);

CREATE POLICY "Deny anon insert on weekly_videos"
    ON weekly_videos FOR INSERT
    TO anon
    WITH CHECK (false);

CREATE POLICY "Deny anon update on weekly_videos"
    ON weekly_videos FOR UPDATE
    TO anon
    USING (false);

CREATE POLICY "Deny anon delete on weekly_videos"
    ON weekly_videos FOR DELETE
    TO anon
    USING (false);

-- social_posts policies
CREATE POLICY "Deny anon select on social_posts"
    ON social_posts FOR SELECT
    TO anon
    USING (false);

CREATE POLICY "Deny anon insert on social_posts"
    ON social_posts FOR INSERT
    TO anon
    WITH CHECK (false);

CREATE POLICY "Deny anon update on social_posts"
    ON social_posts FOR UPDATE
    TO anon
    USING (false);

CREATE POLICY "Deny anon delete on social_posts"
    ON social_posts FOR DELETE
    TO anon
    USING (false);

-- news_sources policies
CREATE POLICY "Deny anon select on news_sources"
    ON news_sources FOR SELECT
    TO anon
    USING (false);

CREATE POLICY "Deny anon insert on news_sources"
    ON news_sources FOR INSERT
    TO anon
    WITH CHECK (false);

CREATE POLICY "Deny anon update on news_sources"
    ON news_sources FOR UPDATE
    TO anon
    USING (false);

CREATE POLICY "Deny anon delete on news_sources"
    ON news_sources FOR DELETE
    TO anon
    USING (false);

-- ondemand_jobs policies
CREATE POLICY "Deny anon select on ondemand_jobs"
    ON ondemand_jobs FOR SELECT
    TO anon
    USING (false);

CREATE POLICY "Deny anon insert on ondemand_jobs"
    ON ondemand_jobs FOR INSERT
    TO anon
    WITH CHECK (false);

CREATE POLICY "Deny anon update on ondemand_jobs"
    ON ondemand_jobs FOR UPDATE
    TO anon
    USING (false);

CREATE POLICY "Deny anon delete on ondemand_jobs"
    ON ondemand_jobs FOR DELETE
    TO anon
    USING (false);

-- news_articles policies (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'news_articles') THEN
        EXECUTE 'CREATE POLICY "Deny anon select on news_articles" ON news_articles FOR SELECT TO anon USING (false)';
        EXECUTE 'CREATE POLICY "Deny anon insert on news_articles" ON news_articles FOR INSERT TO anon WITH CHECK (false)';
        EXECUTE 'CREATE POLICY "Deny anon update on news_articles" ON news_articles FOR UPDATE TO anon USING (false)';
        EXECUTE 'CREATE POLICY "Deny anon delete on news_articles" ON news_articles FOR DELETE TO anon USING (false)';
    END IF;
EXCEPTION WHEN duplicate_object THEN
    -- Policies already exist, skip
    NULL;
END $$;

-- =============================================================================
-- VERIFICATION QUERY
-- =============================================================================
-- Run this to verify RLS is enabled:
--
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
--   AND tablename IN ('weekly_briefings', 'weekly_videos', 'social_posts',
--                     'news_sources', 'ondemand_jobs', 'news_articles');
