-- Maya AI News Anchor - Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Weekly briefings table
CREATE TABLE IF NOT EXISTS weekly_briefings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id VARCHAR(100) UNIQUE NOT NULL,  -- Format: "2026-W04"
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,

    -- Scripts
    local_script TEXT,
    business_script TEXT,
    ai_script TEXT,
    full_script TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'aggregating',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    script_approved_at TIMESTAMPTZ,
    video_approved_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,

    -- Constraints
    UNIQUE(year, week_number)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_briefings_status ON weekly_briefings(status);
CREATE INDEX IF NOT EXISTS idx_briefings_created ON weekly_briefings(created_at DESC);

-- Videos table
CREATE TABLE IF NOT EXISTS weekly_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    briefing_id UUID REFERENCES weekly_briefings(id) ON DELETE CASCADE,
    heygen_video_id VARCHAR(100),
    video_url VARCHAR(2000),
    duration_seconds INTEGER,
    status VARCHAR(50) DEFAULT 'queued',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for video lookups
CREATE INDEX IF NOT EXISTS idx_videos_briefing ON weekly_videos(briefing_id);

-- Social posts tracking
CREATE TABLE IF NOT EXISTS social_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    video_id UUID REFERENCES weekly_videos(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    caption TEXT,
    published_at TIMESTAMPTZ,
    post_url VARCHAR(2000),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for post lookups
CREATE INDEX IF NOT EXISTS idx_posts_video ON social_posts(video_id);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON social_posts(platform);

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

-- Index for news sources
CREATE INDEX IF NOT EXISTS idx_news_sources_type ON news_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_news_sources_category ON news_sources(category);
CREATE INDEX IF NOT EXISTS idx_news_sources_active ON news_sources(is_active);

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

-- Index for on-demand jobs
CREATE INDEX IF NOT EXISTS idx_ondemand_jobs_status ON ondemand_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ondemand_jobs_created ON ondemand_jobs(created_at DESC);

-- News articles cache (optional - for debugging/history)
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    briefing_id UUID REFERENCES weekly_briefings(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,  -- telegram, rss, nitter
    source_name VARCHAR(200) NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    url VARCHAR(2000),
    category VARCHAR(50),  -- local, business, ai_tech
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for article lookups
CREATE INDEX IF NOT EXISTS idx_articles_briefing ON news_articles(briefing_id);
CREATE INDEX IF NOT EXISTS idx_articles_category ON news_articles(category);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================
-- IMPORTANT: For production, run the migration file:
--   database/migrations/001_enable_rls.sql
--
-- This enables RLS on all tables and creates policies that:
-- - Deny all access to anonymous users (anon key)
-- - Allow service_role (backend) full access (bypasses RLS by default)
-- =============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- View for dashboard stats
CREATE OR REPLACE VIEW dashboard_stats AS
SELECT
    COUNT(*) as total_briefings,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_briefings,
    COUNT(*) FILTER (WHERE status IN ('awaiting_script_approval', 'awaiting_video_approval')) as pending_approvals,
    (SELECT COUNT(*) FROM weekly_videos) as total_videos,
    (SELECT COUNT(*) FROM social_posts WHERE status = 'published') as total_posts
FROM weekly_briefings;
