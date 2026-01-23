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

-- Row Level Security (RLS) - Enable for production
-- ALTER TABLE weekly_briefings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE weekly_videos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE social_posts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;

-- Grant access to authenticated users (adjust as needed)
-- CREATE POLICY "Allow all for authenticated" ON weekly_briefings
--     FOR ALL USING (true);

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

-- ==================
-- News Sources Management
-- ==================

CREATE TABLE IF NOT EXISTS news_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- rss, telegram, twitter
    url VARCHAR(500) NOT NULL,
    category VARCHAR(50),  -- local, business, ai_tech
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON news_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON news_sources(enabled);

-- ==================
-- Cron Schedules
-- ==================

CREATE TABLE IF NOT EXISTS cron_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==================
-- On-Demand Jobs
-- ==================

CREATE TABLE IF NOT EXISTS ondemand_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_url VARCHAR(2000) NOT NULL,
    title VARCHAR(500),
    original_content TEXT,

    -- Scripts per language
    script_en TEXT,
    script_ms TEXT,

    -- Videos per language
    video_url_en VARCHAR(2000),
    video_url_ms VARCHAR(2000),

    -- Captions per language
    caption_en TEXT,
    caption_ms TEXT,

    -- Configuration
    languages JSONB DEFAULT '["en"]',
    platforms JSONB DEFAULT '["instagram", "facebook", "tiktok", "youtube"]',

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ondemand_status ON ondemand_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ondemand_created ON ondemand_jobs(created_at DESC);

-- ==================
-- Content Library - Stories
-- ==================

CREATE TABLE IF NOT EXISTS stories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    source_url VARCHAR(2000),
    story_type VARCHAR(50) DEFAULT 'manual',  -- weekly_briefing, on_demand, manual
    status VARCHAR(50) DEFAULT 'draft',  -- draft, script_ready, video_ready, published, archived
    tags JSONB DEFAULT '[]',
    featured BOOLEAN DEFAULT false,

    -- Scripts
    script_en TEXT,
    script_ms TEXT,
    thumbnail_url VARCHAR(2000),

    -- Related IDs
    briefing_id UUID REFERENCES weekly_briefings(id) ON DELETE SET NULL,
    ondemand_job_id UUID REFERENCES ondemand_jobs(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_type ON stories(story_type);
CREATE INDEX IF NOT EXISTS idx_stories_featured ON stories(featured);
CREATE INDEX IF NOT EXISTS idx_stories_created ON stories(created_at DESC);

-- Trigger for updated_at
CREATE TRIGGER stories_updated_at
    BEFORE UPDATE ON stories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ==================
-- Content Library - Video Assets
-- ==================

CREATE TABLE IF NOT EXISTS video_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,  -- 'en' or 'ms'
    video_url VARCHAR(2000) NOT NULL,
    thumbnail_url VARCHAR(2000),
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    heygen_video_id VARCHAR(100),

    -- Quality/format
    resolution VARCHAR(20),  -- e.g., "1080x1920"
    format VARCHAR(10),  -- e.g., "mp4"

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_video_assets_story ON video_assets(story_id);
CREATE INDEX IF NOT EXISTS idx_video_assets_language ON video_assets(language);

-- ==================
-- Content Library - Publish Records
-- ==================

CREATE TABLE IF NOT EXISTS publish_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
    video_id UUID REFERENCES video_assets(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,  -- instagram, facebook, tiktok, youtube
    language VARCHAR(10) NOT NULL,

    -- Post details
    post_url VARCHAR(2000),
    post_id VARCHAR(200),
    caption TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, published, failed
    error TEXT,

    -- Timestamps
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_publish_story ON publish_records(story_id);
CREATE INDEX IF NOT EXISTS idx_publish_platform ON publish_records(platform);
CREATE INDEX IF NOT EXISTS idx_publish_status ON publish_records(status);

-- ==================
-- Content Stats View
-- ==================

CREATE OR REPLACE VIEW content_stats AS
SELECT
    (SELECT COUNT(*) FROM stories) as total_stories,
    (SELECT COUNT(*) FROM stories WHERE status = 'draft') as draft_stories,
    (SELECT COUNT(*) FROM stories WHERE status = 'script_ready') as script_ready_stories,
    (SELECT COUNT(*) FROM stories WHERE status = 'video_ready') as video_ready_stories,
    (SELECT COUNT(*) FROM stories WHERE status = 'published') as published_stories,
    (SELECT COUNT(*) FROM video_assets) as total_videos,
    (SELECT COUNT(*) FROM video_assets WHERE language = 'en') as english_videos,
    (SELECT COUNT(*) FROM video_assets WHERE language = 'ms') as malay_videos,
    (SELECT COUNT(*) FROM publish_records WHERE status = 'published') as total_published,
    (SELECT COUNT(*) FROM stories WHERE created_at >= NOW() - INTERVAL '7 days') as this_week,
    (SELECT COUNT(*) FROM stories WHERE created_at >= NOW() - INTERVAL '30 days') as this_month;
