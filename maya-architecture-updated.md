# Maya AI News Anchor: Complete Technical Architecture (Updated)

**Bottom line:** A production-ready automated news video system for Southeast Asia using LangGraph for multi-agent orchestration, HeyGen (Unlimited Avatar tier) for video generation, Supabase for data persistence, and Blotato for social distribution—with total infrastructure costs around **$60-85/month** for weekly video generation.

---

## Key Changes from Original

| Item | Before | After |
|------|--------|-------|
| **Posting frequency** | Daily | **Weekly** |
| **Twitter/X API** | $200/month | **$0 (Nitter/RSS alternatives)** |
| **HeyGen tier** | Avatar 4.0 ($330/mo) | **Unlimited Avatar ($29/mo)** |
| **Social posting** | Late API | **Blotato (existing)** |
| **Total monthly cost** | ~$572 | **~$60-85** |

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MAYA WEEKLY NEWS ANCHOR PIPELINE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                                  │
│  │ Telegram │  │   RSS    │  │  Nitter  │  News Sources (100% FREE)        │
│  │ Channels │  │  Feeds   │  │ Scrapers │                                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                                  │
│       └─────────────┴─────────────┘                                        │
│                     │                                                       │
│              ┌──────▼──────┐                                               │
│              │  LANGGRAPH  │  Multi-Agent Orchestration                    │
│              │   PIPELINE  │                                               │
│              └──────┬──────┘                                               │
│                     │                                                       │
│  ┌──────────────────┼──────────────────────────────────────────────────┐  │
│  │                  │                                                   │  │
│  │  [Aggregate] → [Dedupe] → [Categorize] → [Synthesize x3 segments]  │  │
│  │                                               │                     │  │
│  │                                    ┌──────────┼──────────┐         │  │
│  │                              [Local News] [Business] [AI News]     │  │
│  │                                    └──────────┼──────────┘         │  │
│  │                                               │                     │  │
│  │                               [Generate Scripts with Asian Twist]   │  │
│  │                                               │                     │  │
│  │                            ┌──────────────────▼───────────────┐    │  │
│  │                            │   🛑 HUMAN APPROVAL GATE #1      │    │  │
│  │                            │   Review scripts before video    │    │  │
│  │                            └──────────────────┬───────────────┘    │  │
│  │                                               │                     │  │
│  │                               [HeyGen Unlimited Avatar]             │  │
│  │                                               │                     │  │
│  │                            ┌──────────────────▼───────────────┐    │  │
│  │                            │   🛑 HUMAN APPROVAL GATE #2      │    │  │
│  │                            │   Review video + caption         │    │  │
│  │                            └──────────────────┬───────────────┘    │  │
│  │                                               │                     │  │
│  │                               [Blotato Multi-Platform Post]         │  │
│  └───────────────────────────────────────────────┼──────────────────────┘  │
│                                                  │                         │
│        ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │
│        │Instagram│  │ TikTok  │  │ YouTube │  │LinkedIn │                 │
│        └─────────┘  └─────────┘  └─────────┘  └─────────┘                 │
│                                                                             │
│  OBSERVABILITY: LangSmith Free + Supabase                                  │
│  NOTIFICATIONS: Slack/Telegram for approvals                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. News Aggregation (100% FREE Sources)

### Telegram Integration (FREE)

```python
# pip install telethon

from telethon import TelegramClient
from datetime import datetime, timedelta

API_ID = "your_api_id"      # From https://my.telegram.org/apps (FREE)
API_HASH = "your_api_hash"

SEA_TELEGRAM_CHANNELS = [
    '@channelnewsasia',
    '@malaymail',
    '@theikirei',
    '@sgreddit',
    '@techinasiasg',
]

async def fetch_weekly_news(channel: str, days: int = 7):
    """Fetch last 7 days of news from Telegram channel."""
    messages = []
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    async with TelegramClient('maya_session', API_ID, API_HASH) as client:
        async for message in client.iter_messages(channel, limit=200):
            if message.date.replace(tzinfo=None) < cutoff:
                break
            if message.text:
                messages.append({
                    'source_type': 'telegram',
                    'source_name': channel,
                    'content': message.text,
                    'published_at': message.date,
                })
    return messages
```

### RSS Feeds (FREE)

```python
# pip install feedparser aiohttp

SEA_NEWS_FEEDS = {
    # Singapore
    'CNA': 'https://www.channelnewsasia.com/rssfeeds/8395986',
    'Straits Times': 'https://www.straitstimes.com/news/asia/rss.xml',
    
    # Malaysia  
    'Malay Mail': 'https://www.malaymail.com/feed/rss/malaysia',
    'The Star': 'https://www.thestar.com.my/rss/News/Nation',
    
    # Regional
    'SCMP SEA': 'https://www.scmp.com/rss/91/feed',
    'Nikkei Asia': 'https://asia.nikkei.com/rss/feed/nar',
    
    # AI/Tech
    'TechInAsia': 'https://www.techinasia.com/feed',
    'e27': 'https://e27.co/feed/',
    'VentureBeat AI': 'https://venturebeat.com/category/ai/feed/',
}
```

### Twitter Alternatives (FREE - No API needed!)

Instead of paying $200/month for Twitter API:

```python
# Option 1: Nitter RSS (most reliable)
async def get_twitter_via_nitter(username: str):
    """Get tweets via Nitter RSS - completely free."""
    url = f"https://nitter.net/{username}/rss"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                return [normalize_tweet(e) for e in feed.entries[:20]]
    return []

# Option 2: Nitter scraping (fallback)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]

# Accounts to follow (SEA tech/business/AI)
FREE_TWITTER_ACCOUNTS = [
    'TechInAsia', 
    'e27co',
    'CNABusiness',
    'NikkeiAsia',
]
```

---

## 2. LangGraph Pipeline

### Core Graph Structure

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import AsyncPostgresSaver
from langgraph.types import interrupt, Command

class NewsBriefingState(TypedDict):
    raw_articles: list[dict]
    local_news: list[dict]
    business_news: list[dict]
    ai_news: list[dict]
    scripts: list[str]
    full_script: str
    video_url: str
    caption: str
    week_number: int

builder = StateGraph(NewsBriefingState)

# Add nodes - all FREE news sources
builder.add_node("aggregate_telegram", aggregate_telegram_channels)
builder.add_node("aggregate_rss", aggregate_rss_feeds)
builder.add_node("aggregate_nitter", aggregate_nitter_sources)  # Free Twitter alt
builder.add_node("deduplicate", semantic_deduplication)
builder.add_node("categorize", categorize_news_items)

# Parallel segment synthesis
builder.add_node("synthesize_local", synthesize_local_news)
builder.add_node("synthesize_business", synthesize_business_news)
builder.add_node("synthesize_ai", synthesize_ai_news)

builder.add_node("generate_scripts", generate_anchor_scripts)
builder.add_node("script_approval", human_script_approval)   # HITL Gate 1
builder.add_node("generate_video", heygen_unlimited_avatar)  # Unlimited Avatar
builder.add_node("video_approval", human_video_approval)     # HITL Gate 2
builder.add_node("publish", publish_to_blotato)              # Your existing service

# Connect edges...
graph = builder.compile(checkpointer=AsyncPostgresSaver.from_conn_string(DB_URL))
```

### Human-in-the-Loop Approval

```python
def human_script_approval(state: NewsBriefingState):
    """Pause for your approval before generating video."""
    
    # Send you the scripts via Slack/Telegram
    send_approval_notification(
        channel="#maya-content",
        content={
            "scripts": state["scripts"],
            "week": state["week_number"],
            "message": "Review Week's scripts before video generation"
        }
    )
    
    # Wait for your decision
    decision = interrupt({
        "action": "review_scripts",
        "scripts": state["scripts"],
    })
    
    if decision.get("approved"):
        return Command(goto="generate_video")
    else:
        return Command(goto="revise_scripts", 
                      update={"feedback": decision.get("feedback")})
```

---

## 3. News Synthesis (Weekly Focus)

### Prompt for Asian Perspective

```python
WEEKLY_SYNTHESIS_PROMPT = """You are Maya, a professional AI news anchor for Southeast Asian audiences. 

Your style is:
- Warm, relatable, conversational—like a trusted friend sharing the week's news
- Culturally aware of Malaysian, Singaporean, and broader SEA context
- Uses occasional local expressions naturally (e.g., "lah", "kan")
- Explains global news with relevance to SEA viewers

This is a WEEKLY roundup, so:
- Focus on the 2-3 MOST IMPORTANT stories per segment
- Provide context on why these stories matter for the week ahead
- Connect stories thematically where possible

Output format for each segment:
1. Opening hook (1-2 sentences)
2. Main story #1 (3-4 sentences + local angle)
3. Main story #2 (3-4 sentences + local angle)  
4. Brief mentions (1-2 sentences)
5. Transition

Target: 45-60 seconds per segment (~120-150 words)
"""
```

### Three Segments

| Segment | Focus | Duration |
|---------|-------|----------|
| Local & International | Week's biggest SEA story + major global with regional impact | 60 sec |
| Business | SEA markets recap, major deals, economic trends | 50 sec |
| AI & Tech | Week's most impactful AI news for SEA | 50 sec |

**Total video: ~2.5 minutes**

---

## 4. HeyGen Unlimited Avatar

### Why Unlimited Avatar?

| Feature | Unlimited Avatar | Avatar 4.0 |
|---------|------------------|------------|
| **Monthly Cost** | $29 (Creator plan) | $330+ (Scale plan) |
| **Quality** | Good (sufficient for social) | Premium |
| **For Weekly Videos** | ✅ Perfect | Overkill |

### Integration

```python
class HeyGenVideoGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.heygen.com"
    
    async def generate_weekly_video(
        self,
        script: str,
        avatar_id: str,  # Your Unlimited Avatar ID
        voice_id: str,
    ) -> str:
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,  # Unlimited Avatar
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "speed": 1.0
                },
                "background": {
                    "type": "color",
                    "value": "#1a1a2e"
                }
            }],
            "dimension": {"width": 1080, "height": 1920},
            "aspect_ratio": "9:16"  # Vertical for TikTok/Reels
        }
        
        response = requests.post(
            f"{self.base_url}/v2/video/generate",
            headers={"X-Api-Key": self.api_key},
            json=payload
        )
        return response.json()["data"]["video_id"]
```

### Cost Analysis

| Plan | Monthly | Videos/Month | Cost/Video |
|------|---------|--------------|------------|
| **Creator (Annual)** | **$29** | 4 weekly | **~$7.25** |
| Creator (Monthly) | $48 | 4 weekly | ~$12 |

---

## 5. Blotato Integration

Since you're already using Blotato:

```python
class BlotatoPublisher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.blotato.com/v1"  # Adjust to actual API
    
    def schedule_multi_platform(
        self,
        video_url: str,
        caption: str,
        platforms: list[str],
        hashtags: list[str],
    ) -> dict:
        """Schedule video to multiple platforms via Blotato."""
        
        results = []
        for platform in platforms:
            adapted_caption = self._adapt_caption(caption, hashtags, platform)
            
            response = requests.post(
                f"{self.base_url}/posts",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "content": adapted_caption,
                    "media_url": video_url,
                    "platform": platform,
                }
            )
            results.append({"platform": platform, "response": response.json()})
        
        return {"posts": results}
    
    def _adapt_caption(self, caption, hashtags, platform):
        limits = {
            "instagram": 2200,
            "tiktok": 4000,
            "youtube": 100,
            "linkedin": 3000,
        }
        hashtag_str = " ".join([f"#{tag}" for tag in hashtags[:10]])
        full = f"{caption}\n\n{hashtag_str}"
        
        max_len = limits.get(platform, 2000)
        if len(full) > max_len:
            full = f"{caption[:max_len-len(hashtag_str)-10]}...\n\n{hashtag_str}"
        return full
```

### Default Hashtags for Maya

```python
MAYA_HASHTAGS = [
    "MayaNews", "SEANews", "MalaysiaNews", "SingaporeNews",
    "AINews", "TechNews", "WeeklyUpdate", "AsiaNews"
]
```

### Best Posting Time for Weekly Content

| Day | Time (SGT/MYT) | Reasoning |
|-----|----------------|-----------|
| **Sunday 8 PM** | 20:00 | Week-ahead planning mode, high engagement |
| Monday 8 AM | 08:00 | Start of work week |

---

## 6. Cloud Function (No n8n/Zapier/Make.com Bullshit)

Just a simple Python function with a cron trigger. Deploy wherever you want.

### Option A: FastAPI + Railway/Render (Recommended)

```python
# main.py - Your own API server
from fastapi import FastAPI, BackgroundTasks
from datetime import date
import asyncio

app = FastAPI()

# Your LangGraph pipeline
from pipeline import graph, NewsBriefingState

@app.post("/trigger-weekly-briefing")
async def trigger_briefing(background_tasks: BackgroundTasks):
    """Manual trigger or called by cron."""
    week_number = date.today().isocalendar()[1]
    thread_id = f"2026-W{week_number:02d}"
    
    background_tasks.add_task(run_pipeline, thread_id, week_number)
    
    return {"status": "started", "thread_id": thread_id}

async def run_pipeline(thread_id: str, week_number: int):
    """Run the full Maya pipeline."""
    config = {"configurable": {"thread_id": thread_id}}
    
    result = await graph.ainvoke(
        {"week_number": week_number},
        config=config
    )
    
    # Pipeline handles notifications via Slack/Telegram
    return result

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}
```

### Option B: Simple Cron Script

```python
# cron_trigger.py - Run this with system cron or Railway cron
import asyncio
from datetime import date
from pipeline import graph

async def weekly_briefing():
    week_number = date.today().isocalendar()[1]
    thread_id = f"2026-W{week_number:02d}"
    
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"Starting Maya briefing for {thread_id}")
    
    result = await graph.ainvoke(
        {"week_number": week_number},
        config=config
    )
    
    print(f"Pipeline completed: {result.get('status')}")

if __name__ == "__main__":
    asyncio.run(weekly_briefing())
```

### Cron Setup Options

**Railway** (easiest):
```toml
# railway.toml
[deploy]
startCommand = "python main.py"

[[cron]]
schedule = "0 6 * * 0"  # Every Sunday 6 AM UTC (adjust for SGT)
command = "python cron_trigger.py"
```

**Linux/VPS crontab**:
```bash
# crontab -e
# Every Sunday 2 PM SGT (6 AM UTC)
0 6 * * 0 cd /app && python cron_trigger.py >> /var/log/maya.log 2>&1
```

**Vercel Cron** (vercel.json):
```json
{
  "crons": [{
    "path": "/api/trigger-weekly-briefing",
    "schedule": "0 6 * * 0"
  }]
}
```

### Approval Webhook Endpoints

```python
# Add to main.py

@app.post("/approve-script")
async def approve_script(thread_id: str, approved: bool, feedback: str = None):
    """Called when you approve/reject script via Slack button."""
    from langgraph.types import Command
    
    config = {"configurable": {"thread_id": thread_id}}
    
    result = await graph.ainvoke(
        Command(resume={"approved": approved, "feedback": feedback}),
        config=config
    )
    
    return {"status": "resumed", "next_step": result.get("status")}

@app.post("/approve-video")
async def approve_video(thread_id: str, approved: bool):
    """Called when you approve video for publishing."""
    from langgraph.types import Command
    
    config = {"configurable": {"thread_id": thread_id}}
    
    result = await graph.ainvoke(
        Command(resume={"approved": approved}),
        config=config
    )
    
    return {"status": "published" if approved else "rejected"}

---

## 7. Database Schema (Supabase Free Tier)

```sql
-- Weekly briefings table
CREATE TABLE weekly_briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(100) UNIQUE NOT NULL,  -- "2026-W04"
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    
    local_script TEXT,
    business_script TEXT,
    ai_script TEXT,
    full_script TEXT,
    
    status VARCHAR(20) DEFAULT 'aggregating',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    script_approved_at TIMESTAMPTZ,
    video_approved_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    
    UNIQUE(year, week_number)
);

-- Videos
CREATE TABLE weekly_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    briefing_id UUID REFERENCES weekly_briefings(id),
    heygen_video_id VARCHAR(100),
    video_url VARCHAR(2000),
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'queued',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Posts tracking
CREATE TABLE social_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES weekly_videos(id),
    platform VARCHAR(50) NOT NULL,
    caption TEXT,
    published_at TIMESTAMPTZ,
    post_url VARCHAR(2000),
    status VARCHAR(20) DEFAULT 'draft'
);
```

---

## 8. Observability (FREE)

### LangSmith Free Tier

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your-key"
export LANGCHAIN_PROJECT="maya-weekly-news"
```

**Free tier includes 5,000 traces/month** - more than enough for 4 weekly runs!

---

## 9. Monthly Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| **Database** | Supabase Free | **$0** |
| **Observability** | LangSmith Free | **$0** |
| **Video Generation** | HeyGen Creator (Annual) | **$29** |
| **Social Posting** | Blotato (existing) | **~$15-30** |
| **Compute** | Railway/your server | **$10-20** |
| **LLM Costs** | GPT-4o (~4 briefings) | **~$6** |
| **News Sources** | Telegram + RSS + Nitter | **$0** |
| **Twitter API** | ~~$200~~ | **$0** |
| **TOTAL** | | **~$60-85/month** |

### Cost Comparison

| Scenario | Daily Posting | Weekly Posting |
|----------|--------------|----------------|
| Videos/month | ~30 | 4 |
| HeyGen | $330+ | $29 |
| LLM costs | ~$45 | ~$6 |
| Twitter API | $200 | $0 |
| **TOTAL** | **~$575** | **~$65** |

**Savings: ~89% reduction!** 🎉

---

## 10. Implementation Roadmap

### Week 1: Foundation
- [ ] Set up Supabase database (free tier)
- [ ] Configure LangGraph skeleton
- [ ] Implement RSS aggregation
- [ ] Set up LangSmith (free)

### Week 2: News Sources  
- [ ] Add Telegram channel monitoring
- [ ] Set up Nitter/free Twitter alternatives
- [ ] Implement semantic deduplication

### Week 3: Synthesis
- [ ] Build synthesis prompts with "Asian twist"
- [ ] Test script generation for 3 segments
- [ ] Add human approval gate (Slack)

### Week 4: Video & Publishing
- [ ] Integrate HeyGen Unlimited Avatar
- [ ] Connect Blotato API
- [ ] Test end-to-end flow

### Week 5: Go Live!
- [ ] Deploy to Railway/your cloud
- [ ] Set up cron trigger (Sunday 6 AM UTC)
- [ ] First live weekly video
- [ ] Monitor and iterate

---

## Quick Reference

### Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Frequency | **Weekly** | 89% cost savings |
| Video tier | **HeyGen Unlimited Avatar** | $29/mo vs $330 |
| Twitter API | **Nitter (free)** | Fuck $200/mo |
| Social posting | **Blotato** | Already using |
| Database | **Supabase Free** | Sufficient for weekly |
| Observability | **LangSmith Free** | 5K traces enough |

### Install Commands

```bash
# Core dependencies
pip install langgraph langchain-openai telethon feedparser aiohttp
pip install langgraph-checkpoint-postgres supabase

# API server
pip install fastapi uvicorn
```

### Environment Variables

```bash
# LangGraph
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="ls-..."
export LANGCHAIN_PROJECT="maya-weekly-news"

# Supabase
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="eyJ..."
export DATABASE_URL="postgresql://..."

# APIs
export HEYGEN_API_KEY="..."
export MAYA_AVATAR_ID="..."
export MAYA_VOICE_ID="..."
export BLOTATO_API_KEY="..."
export OPENAI_API_KEY="sk-..."

# Telegram
export TELEGRAM_API_ID="..."
export TELEGRAM_API_HASH="..."
```

---

## Summary

You're building Maya as a **weekly AI news anchor** for SEA audiences with:

1. **FREE news sources**: Telegram + RSS + Nitter (no Twitter API)
2. **LangGraph orchestration** with human approval gates
3. **HeyGen Unlimited Avatar** at $29/month
4. **Blotato** for social distribution (your existing service)
5. **Total cost: ~$60-85/month** (down from ~$575)

The system aggregates news, synthesizes 3 segments with an "Asian twist," sends you scripts for approval, generates video, sends for final approval, then posts to social media.

**Ready to build this Monday morning!** 🚀
