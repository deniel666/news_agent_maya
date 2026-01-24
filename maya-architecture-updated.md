# Maya AI News Anchor: Complete Technical Architecture

**Overview:** A production-ready automated news video system for Southeast Asia using LangGraph for multi-agent orchestration, HeyGen for AI avatar video generation, Supabase for data persistence, and Blotato for social distribution.

**Monthly Cost:** ~$60-85 for weekly video generation

---

## Table of Contents

1. [Key Changes from Original](#1-key-changes-from-original)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture](#4-frontend-architecture)
5. [LangGraph Pipeline](#5-langgraph-pipeline)
6. [External Integrations](#6-external-integrations)
7. [Database Schema](#7-database-schema)
8. [News Sources](#8-news-sources)
9. [Scheduling & Automation](#9-scheduling--automation)
10. [Notification Systems](#10-notification-systems)
11. [Testing Infrastructure](#11-testing-infrastructure)
12. [Deployment](#12-deployment)
13. [Cost Analysis](#13-cost-analysis)
14. [Feature Summary](#14-feature-summary)
15. [Roadmap](#15-roadmap)

---

## 1. Key Changes from Original

| Item | Before | After |
|------|--------|-------|
| **Posting frequency** | Daily | **Weekly** |
| **Twitter/X API** | $200/month | **$0 (Nitter/RSS alternatives)** |
| **HeyGen tier** | Avatar 4.0 ($330/mo) | **Unlimited Avatar ($29/mo)** |
| **Social posting** | Late API | **Blotato (existing)** |
| **Total monthly cost** | ~$572 | **~$60-85** |

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MAYA AI NEWS ANCHOR SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         FRONTEND (React + TypeScript)                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │Dashboard │ │Briefings │ │Approvals │ │On-Demand │ │ Sources  │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                                │   │
│  │  │ Schedule │ │Analytics │ │ Settings │  ←── WebSocket Real-time       │   │
│  │  └──────────┘ └──────────┘ └──────────┘                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                              REST API + WS                                      │
│                                    │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         BACKEND (FastAPI + Python)                       │   │
│  │                                                                          │   │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    API LAYER (REST + WebSocket)                     │ │   │
│  │  │  /briefings  /approvals  /dashboard  /sources  /schedule           │ │   │
│  │  │  /on-demand  /settings   /telegram   /cron     /ws                 │ │   │
│  │  └────────────────────────────────────────────────────────────────────┘ │   │
│  │                                    │                                     │   │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                      SERVICES LAYER                                 │ │   │
│  │  │  DatabaseService │ NewsAggregator │ NotificationService            │ │   │
│  │  │  TelegramBot     │ OnDemandService                                 │ │   │
│  │  └────────────────────────────────────────────────────────────────────┘ │   │
│  │                                    │                                     │   │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                   LANGGRAPH PIPELINE (Agents)                       │ │   │
│  │  │  Aggregate → Dedupe → Categorize → Synthesize → Video → Publish    │ │   │
│  │  └────────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────┐   │
│  │ Supabase │  HeyGen  │ Blotato  │  OpenAI  │ Telegram │    LangSmith     │   │
│  │    DB    │  Video   │  Social  │  GPT-4o  │   Bot    │   Observability  │   │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────────────┘   │
│                                                                                 │
│  NEWS SOURCES (All Free):                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                                      │
│  │ Telegram │  │   RSS    │  │  Nitter  │                                      │
│  │ Channels │  │  Feeds   │  │ (Twitter)│                                      │
│  └──────────┘  └──────────┘  └──────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Backend Architecture

### 3.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI (Python 3.11+) |
| Server | Uvicorn with async support |
| Agent Orchestration | LangGraph with memory checkpointing |
| Database | Supabase (PostgreSQL) with mock mode fallback |
| LLM | OpenAI GPT-4o |
| Task Execution | Async/await with BackgroundTasks |

### 3.2 API Endpoints

**Base URL:** `/api/v1`

#### Briefings API (`/briefings`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create new weekly briefing (runs pipeline in background) |
| GET | `/` | List all briefings with pagination and status filtering |
| GET | `/pending` | List briefings awaiting approval |
| GET | `/current` | Get current week's briefing |
| GET | `/{thread_id}` | Get specific briefing with pipeline state |
| GET | `/{thread_id}/scripts` | Get all three scripts (local, business, AI) |
| GET | `/{thread_id}/video` | Get video details for briefing |
| GET | `/{thread_id}/posts` | Get social media posts for briefing |
| DELETE | `/{thread_id}` | Delete briefing (requires admin API key) |

#### Approvals API (`/approvals`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/script` | Approve/reject scripts with optional edits and feedback |
| POST | `/video` | Approve/reject video for publishing |
| GET | `/pending` | Get all pending approvals (scripts & videos) |
| POST | `/slack/interactive` | Handle Slack button clicks |

#### Dashboard API (`/dashboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | Dashboard statistics (totals, completions, pending) |
| GET | `/recent-activity` | Recent pipeline activity log |
| GET | `/weekly-summary` | 4-week summary view |
| GET | `/pipeline-status/{thread_id}` | Detailed pipeline stages and status |
| GET | `/sources-status` | Status of all configured news sources |

#### Sources API (`/sources`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all news sources with filtering |
| POST | `/` | Add new news source (RSS, Telegram, Twitter/Nitter) |
| GET | `/{source_id}` | Get specific source |
| PATCH | `/{source_id}` | Update source configuration |
| DELETE | `/{source_id}` | Delete source |
| POST | `/{source_id}/toggle` | Enable/disable source |
| POST | `/{source_id}/test` | Test fetch from source |
| POST | `/import/defaults` | Import default SEA news sources |

#### Scheduling API (`/cron`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all cron schedules |
| POST | `/` | Create new cron schedule with validation |
| PATCH | `/{schedule_id}` | Update schedule |
| DELETE | `/{schedule_id}` | Delete schedule |
| POST | `/{schedule_id}/toggle` | Enable/disable schedule |
| POST | `/{schedule_id}/run-now` | Manually trigger schedule |
| GET | `/presets/common` | Common cron presets |
| POST | `/validate` | Validate cron expression |

#### On-Demand API (`/on-demand`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate video from specific article URL |
| GET | `/jobs` | List on-demand jobs with status filtering |
| GET | `/jobs/{job_id}` | Get job details with scripts/videos |
| POST | `/jobs/{job_id}/approve` | Approve/reject script |
| POST | `/jobs/{job_id}/approve-video` | Approve video for publishing |
| POST | `/jobs/{job_id}/regenerate` | Regenerate script or video |
| DELETE | `/jobs/{job_id}` | Delete on-demand job |

#### Settings API (`/settings`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Integration configuration status |
| GET | `/avatars` | List available HeyGen avatars |
| GET | `/voices` | List available HeyGen voices |
| GET | `/social-accounts` | List connected Blotato accounts |
| GET | `/current-config` | Get non-sensitive configuration |
| POST | `/test-connection` | Test service connections |

#### Telegram API (`/telegram`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook` | Receive Telegram webhook updates |
| GET | `/setup` | Set up Telegram webhook |
| DELETE | `/webhook` | Remove Telegram webhook |
| GET | `/info` | Get current webhook info |

#### WebSocket (`/ws`)

| Endpoint | Description |
|----------|-------------|
| `WS /ws/{thread_id}` | Real-time pipeline updates with heartbeat |

### 3.3 Services Layer

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SERVICES LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │   DatabaseService   │    │  NewsAggregator     │                │
│  │                     │    │                     │                │
│  │  - Mock mode support│    │  - RSS feeds (9+)   │                │
│  │  - Briefings CRUD   │    │  - Nitter scraping  │                │
│  │  - Videos tracking  │    │  - Telegram channels│                │
│  │  - Posts management │    │  - Deduplication    │                │
│  │  - Dashboard stats  │    │  - 7-day lookback   │                │
│  └─────────────────────┘    └─────────────────────┘                │
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │ NotificationService │    │  TelegramBotService │                │
│  │                     │    │                     │                │
│  │  - Slack messages   │    │  - Webhook handling │                │
│  │  - Telegram alerts  │    │  - Inline keyboards │                │
│  │  - Approval buttons │    │  - Video sending    │                │
│  │  - Rich formatting  │    │  - Commands handler │                │
│  └─────────────────────┘    └─────────────────────┘                │
│                                                                     │
│  ┌─────────────────────┐                                           │
│  │   OnDemandService   │                                           │
│  │                     │                                           │
│  │  - Article scraping │                                           │
│  │  - Multi-language   │                                           │
│  │  - Script generation│                                           │
│  │  - Job tracking     │                                           │
│  └─────────────────────┘                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.4 Authentication

The system uses API key authentication for administrative operations:

| Header | Description |
|--------|-------------|
| `X-Admin-API-Key` | Required for DELETE operations on briefings |

Configuration via `ADMIN_API_KEY` environment variable.

---

## 4. Frontend Architecture

### 4.1 Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | React 18 with TypeScript |
| Build Tool | Vite |
| Routing | React Router v6 |
| State Management | TanStack React Query v5 |
| HTTP Client | Axios |
| UI Framework | Tailwind CSS |
| Icons | Lucide React |

### 4.2 Page Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FRONTEND PAGES                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Dashboard   │  │  Briefings   │  │  Approvals   │              │
│  │              │  │              │  │              │              │
│  │ - Statistics │  │ - List view  │  │ - Scripts    │              │
│  │ - Activity   │  │ - Filtering  │  │ - Videos     │              │
│  │ - Summary    │  │ - Pagination │  │ - Edit mode  │              │
│  │ - New button │  │ - Details    │  │ - Actions    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  On-Demand   │  │   Sources    │  │   Schedule   │              │
│  │              │  │              │  │              │              │
│  │ - URL input  │  │ - List/CRUD  │  │ - Cron jobs  │              │
│  │ - Languages  │  │ - Type filter│  │ - Enable/off │              │
│  │ - Platforms  │  │ - Test fetch │  │ - Run now    │              │
│  │ - Job status │  │ - Import     │  │ - Presets    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │  Analytics   │  │   Settings   │                                │
│  │              │  │              │                                │
│  │ - Success %  │  │ - Status     │                                │
│  │ - Trends     │  │ - Test conn  │                                │
│  │ - Charts     │  │ - Avatars    │                                │
│  │ - Metrics    │  │ - Voices     │                                │
│  └──────────────┘  └──────────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Key Features

| Page | Features |
|------|----------|
| **Dashboard** | Key statistics, recent activity feed, 4-week summary, quick actions |
| **Briefings** | Full list with filtering, pagination, status badges, detail navigation |
| **BriefingDetail** | Three scripts display, video preview, social posts, WebSocket live updates |
| **Approvals** | Split view (scripts/videos), inline editing, approve/reject buttons |
| **On-Demand** | Article URL input, multi-language (EN/MS), platform selection, job tracking |
| **Sources** | CRUD operations, type filtering, test fetch, import defaults |
| **Schedule** | Cron management, presets dropdown, manual trigger, validation |
| **Analytics** | Success rates, processing times, status breakdown, trend charts |
| **Settings** | Integration status cards, connection testing, avatar/voice selection |

### 4.4 Real-time Updates

The frontend connects to WebSocket at `/ws/{thread_id}` for live pipeline status updates during briefing generation.

---

## 5. LangGraph Pipeline

### 5.1 Pipeline State

The pipeline maintains state with the following key fields:

| Field | Description |
|-------|-------------|
| `week_number`, `year` | Target week and year |
| `thread_id` | Unique identifier (YYYY-WXX format) |
| `raw_articles` | Aggregated news articles |
| `local_news`, `business_news`, `ai_news` | Categorized articles |
| `local_script`, `business_script`, `ai_script` | Synthesized scripts |
| `full_script` | Combined final script |
| `heygen_video_id`, `video_url` | Video generation tracking |
| `status` | Current pipeline stage |
| `script_approved`, `video_approved` | Approval flags |

### 5.2 Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          LANGGRAPH PIPELINE FLOW                             │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   START                                                                      │
│     │                                                                        │
│     ▼                                                                        │
│ ┌─────────────┐                                                              │
│ │  AGGREGATE  │  Fetch from RSS, Nitter, Telegram (7-day lookback)          │
│ └──────┬──────┘                                                              │
│        │                                                                     │
│        ▼                                                                     │
│ ┌─────────────┐                                                              │
│ │ DEDUPLICATE │  Remove near-duplicate articles by title similarity         │
│ └──────┬──────┘                                                              │
│        │                                                                     │
│        ▼                                                                     │
│ ┌─────────────┐                                                              │
│ │ CATEGORIZE  │  GPT classifies: local, business, ai_tech                   │
│ └──────┬──────┘                                                              │
│        │                                                                     │
│        ├──────────────┬──────────────┐                                       │
│        ▼              ▼              ▼                                       │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐                                │
│ │ SYNTHESIZE │ │ SYNTHESIZE │ │ SYNTHESIZE │  Parallel GPT calls            │
│ │   LOCAL    │ │  BUSINESS  │ │   AI/TECH  │                                │
│ │  (60 sec)  │ │  (50 sec)  │ │  (50 sec)  │                                │
│ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘                                │
│       └──────────────┼──────────────┘                                        │
│                      ▼                                                       │
│            ┌─────────────────┐                                               │
│            │ GENERATE SCRIPTS│  Combine with intro/outro + caption          │
│            └────────┬────────┘                                               │
│                     │                                                        │
│                     ▼                                                        │
│   ┌─────────────────────────────────────┐                                   │
│   │     HUMAN APPROVAL GATE #1          │  Send to Slack/Telegram           │
│   │         (Script Review)             │  Wait for approve/reject          │
│   └────────────────┬────────────────────┘                                   │
│                    │                                                         │
│            ┌───────┴───────┐                                                │
│            │               │                                                │
│       [Approved]      [Rejected]                                            │
│            │               │                                                │
│            ▼               ▼                                                │
│   ┌─────────────────┐  ┌──────┐                                             │
│   │ GENERATE VIDEO  │  │ FAIL │                                             │
│   │    (HeyGen)     │  └──────┘                                             │
│   └────────┬────────┘                                                        │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────┐                                   │
│   │     HUMAN APPROVAL GATE #2          │  Send video preview               │
│   │         (Video Review)              │  Wait for approve/reject          │
│   └────────────────┬────────────────────┘                                   │
│                    │                                                         │
│            ┌───────┴───────┐                                                │
│            │               │                                                │
│       [Approved]      [Rejected]                                            │
│            │               │                                                │
│            ▼               ▼                                                │
│   ┌─────────────────┐  ┌──────┐                                             │
│   │ PUBLISH SOCIAL  │  │ FAIL │                                             │
│   │   (Blotato)     │  └──────┘                                             │
│   └────────┬────────┘                                                        │
│            │                                                                 │
│            ▼                                                                 │
│          END                                                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Pipeline Stages

| Stage | Status Value | Description |
|-------|--------------|-------------|
| 1 | `aggregating` | Fetching news from all sources |
| 2 | `categorizing` | GPT classifying articles |
| 3 | `synthesizing` | Generating three script segments |
| 4 | `awaiting_script_approval` | Waiting for human review |
| 5 | `generating_video` | HeyGen processing (up to 10 min) |
| 6 | `awaiting_video_approval` | Waiting for video review |
| 7 | `publishing` | Posting to social platforms |
| 8 | `completed` | Pipeline finished successfully |
| - | `failed` | Pipeline encountered error or rejection |

### 5.4 Script Specifications

| Segment | Duration | Word Count | Focus |
|---------|----------|------------|-------|
| Local & International | 60 sec | 120-150 words | SEA stories + global with regional impact |
| Business | 50 sec | 100-130 words | SEA markets, deals, economic trends |
| AI & Tech | 50 sec | 100-130 words | Week's impactful AI news for SEA |

**Total video duration:** ~2.5 minutes

### 5.5 Maya Persona

Maya is characterized as a professional AI news anchor with:
- Warm, relatable, conversational style
- Cultural awareness of Malaysian, Singaporean, and broader SEA context
- Natural use of local expressions (e.g., "lah", "kan")
- Ability to explain global news with relevance to SEA viewers

---

## 6. External Integrations

### 6.1 HeyGen (Video Generation)

| Feature | Details |
|---------|---------|
| API Endpoint | `https://api.heygen.com` |
| Authentication | X-Api-Key header |
| Plan | Unlimited Avatar (Creator tier) |
| Cost | $29/month (annual) |

**Capabilities:**
- Generate videos from text scripts
- List available avatars and voices
- Poll video generation status
- Video completion timeout: 600 seconds

**Video Specifications:**

| Parameter | Value |
|-----------|-------|
| Aspect Ratio (Social) | 9:16 (vertical) |
| Aspect Ratio (YouTube) | 16:9 (horizontal) |
| Aspect Ratio (Square) | 1:1 |
| Background | Solid color (#1a1a2e) |
| Voice Speed | 1.0 (normal) |

### 6.2 Blotato (Social Publishing)

| Feature | Details |
|---------|---------|
| API Endpoint | `https://api.blotato.com/v1` |
| Authentication | Bearer token |
| Cost | ~$15-30/month |

**Supported Platforms:**

| Platform | Caption Limit |
|----------|---------------|
| Instagram | 2,200 characters |
| TikTok | 4,000 characters |
| YouTube | 100 characters |
| LinkedIn | 3,000 characters |

**Default Hashtags:** `#MayaNews #SEANews #MalaysiaNews #SingaporeNews #AINews #TechNews #WeeklyUpdate #AsiaNews`

### 6.3 OpenAI (GPT-4o)

| Feature | Details |
|---------|---------|
| Default Model | gpt-4o |
| Temperature | 0.7 (for creative synthesis) |
| Cost | ~$6/month (4 briefings) |

**Used For:**
- News article categorization
- Script synthesis (3 segments)
- Caption generation
- Relevance scoring

### 6.4 Telegram Bot

| Feature | Details |
|---------|---------|
| Mode | Webhook-based |
| Authentication | Bot token |

**Capabilities:**
- Receive webhook updates
- Send approval notifications with inline keyboards
- Send video messages with captions
- Handle callback queries for approvals
- Commands: `/start`, `/status`, `/help`

### 6.5 Slack (Optional)

| Feature | Details |
|---------|---------|
| Mode | Incoming webhooks |
| Channel | Configurable (default: #maya-content) |

**Capabilities:**
- Rich formatted messages
- Interactive buttons for approvals
- Script and video review notifications

### 6.6 LangSmith (Observability)

| Feature | Details |
|---------|---------|
| Tier | Free (5,000 traces/month) |
| Project | maya-weekly-news |

**Provides:**
- Pipeline execution tracing
- LLM call monitoring
- Debug and performance insights

---

## 7. Database Schema

### 7.1 Entity Relationship Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          DATABASE SCHEMA                                  │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────┐                                         │
│  │     weekly_briefings        │                                         │
│  ├─────────────────────────────┤                                         │
│  │ id (UUID) PK                │                                         │
│  │ thread_id (VARCHAR) UNIQUE  │  ←── Format: "YYYY-WXX"                 │
│  │ year (INTEGER)              │                                         │
│  │ week_number (INTEGER)       │                                         │
│  │ local_script (TEXT)         │                                         │
│  │ business_script (TEXT)      │                                         │
│  │ ai_script (TEXT)            │                                         │
│  │ full_script (TEXT)          │                                         │
│  │ status (VARCHAR)            │  ←── Pipeline status enum               │
│  │ created_at (TIMESTAMPTZ)    │                                         │
│  │ script_approved_at          │                                         │
│  │ video_approved_at           │                                         │
│  │ published_at                │                                         │
│  └──────────────┬──────────────┘                                         │
│                 │                                                         │
│                 │ 1:1                                                     │
│                 ▼                                                         │
│  ┌─────────────────────────────┐                                         │
│  │      weekly_videos          │                                         │
│  ├─────────────────────────────┤                                         │
│  │ id (UUID) PK                │                                         │
│  │ briefing_id (UUID) FK       │                                         │
│  │ heygen_video_id (VARCHAR)   │                                         │
│  │ video_url (VARCHAR)         │                                         │
│  │ duration_seconds (INTEGER)  │                                         │
│  │ status (VARCHAR)            │                                         │
│  │ created_at (TIMESTAMPTZ)    │                                         │
│  └──────────────┬──────────────┘                                         │
│                 │                                                         │
│                 │ 1:N                                                     │
│                 ▼                                                         │
│  ┌─────────────────────────────┐                                         │
│  │      social_posts           │                                         │
│  ├─────────────────────────────┤                                         │
│  │ id (UUID) PK                │                                         │
│  │ video_id (UUID) FK          │                                         │
│  │ platform (VARCHAR)          │  ←── instagram, tiktok, youtube, etc.   │
│  │ caption (TEXT)              │                                         │
│  │ published_at (TIMESTAMPTZ)  │                                         │
│  │ post_url (VARCHAR)          │                                         │
│  │ status (VARCHAR)            │  ←── draft, published, failed           │
│  │ created_at (TIMESTAMPTZ)    │                                         │
│  └─────────────────────────────┘                                         │
│                                                                           │
│  ┌─────────────────────────────┐                                         │
│  │     news_articles           │  (Optional - for history/debugging)     │
│  ├─────────────────────────────┤                                         │
│  │ id (UUID) PK                │                                         │
│  │ briefing_id (UUID) FK       │                                         │
│  │ source_type (VARCHAR)       │  ←── telegram, rss, nitter              │
│  │ source_name (VARCHAR)       │                                         │
│  │ title (TEXT)                │                                         │
│  │ content (TEXT)              │                                         │
│  │ url (VARCHAR)               │                                         │
│  │ category (VARCHAR)          │                                         │
│  │ published_at (TIMESTAMPTZ)  │                                         │
│  └─────────────────────────────┘                                         │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Database Views

**dashboard_stats**: Aggregated metrics for the dashboard
- Total briefings count
- Completed briefings count
- Pending approvals count
- Total videos generated
- Total posts published

### 7.3 Mock Database Mode

When Supabase is not configured (development/testing):
- In-memory storage using Python dictionaries
- Same interface as Supabase client
- Enabled when `SUPABASE_URL` contains placeholder values
- Supports full CRUD operations for all entities

---

## 8. News Sources

### 8.1 Source Types

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          NEWS SOURCES                                     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│  │   RSS FEEDS     │  │   NITTER/X      │  │   TELEGRAM      │           │
│  │                 │  │                 │  │                 │           │
│  │ - CNA           │  │ - TechInAsia    │  │ - @channelews   │           │
│  │ - Straits Times │  │ - e27co         │  │   asia          │           │
│  │ - Malay Mail    │  │ - CNABusiness   │  │ - @malaymail    │           │
│  │ - The Star      │  │ - NikkeiAsia    │  │ - @theikirei    │           │
│  │ - SCMP SEA      │  │                 │  │ - @sgreddit     │           │
│  │ - Nikkei Asia   │  │  (Free via      │  │ - @techinasia   │           │
│  │ - TechInAsia    │  │   Nitter RSS)   │  │   sg            │           │
│  │ - e27           │  │                 │  │                 │           │
│  │ - VentureBeat   │  │                 │  │  (Free API)     │           │
│  │                 │  │                 │  │                 │           │
│  │  (All Free)     │  │  (All Free)     │  │                 │           │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘           │
│                                                                           │
│  Total Cost: $0/month                                                     │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Default RSS Feeds

| Source | Region | Category |
|--------|--------|----------|
| CNA | Singapore | General |
| Straits Times | Singapore | General |
| Malay Mail | Malaysia | General |
| The Star | Malaysia | General |
| SCMP SEA | Regional | General |
| Nikkei Asia | Regional | Business |
| TechInAsia | Regional | Tech |
| e27 | Regional | Startups |
| VentureBeat AI | Global | AI/ML |

### 8.3 Source Management Features

- Add/edit/delete sources via API and UI
- Enable/disable individual sources
- Test fetch to verify source works
- Import default SEA sources with one click
- Category assignment (local, business, tech)

---

## 9. Scheduling & Automation

### 9.1 Cron Schedule

**Default Schedule:** Sunday 6 AM UTC (2 PM SGT)

### 9.2 Common Presets

| Schedule | Cron Expression | Description |
|----------|-----------------|-------------|
| Every Sunday 6 AM UTC | `0 6 * * 0` | Default weekly |
| Every Sunday 8 PM SGT | `0 12 * * 0` | Evening option |
| Every Monday 8 AM SGT | `0 0 * * 1` | Start of week |
| Twice weekly | `0 6 * * 0,3` | Wed & Sun |
| Daily at noon SGT | `0 4 * * *` | Daily option |

### 9.3 Trigger Methods

1. **Cron Job**: Automated scheduled trigger
2. **API Call**: POST to `/trigger-weekly-briefing`
3. **Manual UI**: "Run Now" button in Schedule page
4. **CLI Script**: `python cron_trigger.py`

### 9.4 CLI Options

| Option | Description |
|--------|-------------|
| `--week N` | Specify week number |
| `--year YYYY` | Specify year |
| `--api URL` | Trigger via API endpoint |
| `--dry-run` | Preview without executing |

---

## 10. Notification Systems

### 10.1 Notification Flow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     NOTIFICATION SYSTEM                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Pipeline Event                                                           │
│       │                                                                   │
│       ▼                                                                   │
│  ┌──────────────────┐                                                    │
│  │NotificationService│                                                   │
│  └────────┬─────────┘                                                    │
│           │                                                               │
│     ┌─────┴─────┐                                                        │
│     │           │                                                        │
│     ▼           ▼                                                        │
│ ┌───────┐  ┌──────────┐                                                  │
│ │ Slack │  │ Telegram │                                                  │
│ └───┬───┘  └────┬─────┘                                                  │
│     │           │                                                        │
│     ▼           ▼                                                        │
│ ┌───────────────────────────────────────────────────────────────┐       │
│ │                    APPROVAL MESSAGE                            │       │
│ │                                                                │       │
│ │  Week 04 Scripts Ready for Review                             │       │
│ │                                                                │       │
│ │  📍 Local News: [preview text...]                             │       │
│ │  💼 Business:   [preview text...]                             │       │
│ │  🤖 AI & Tech:  [preview text...]                             │       │
│ │                                                                │       │
│ │  ┌──────────┐  ┌──────────┐  ┌──────────────┐                 │       │
│ │  │ Approve  │  │  Reject  │  │  Regenerate  │                 │       │
│ │  └──────────┘  └──────────┘  └──────────────┘                 │       │
│ └───────────────────────────────────────────────────────────────┘       │
│                                                                           │
│  User clicks button → Callback to API → Resume pipeline                  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and show welcome |
| `/status` | Show current pipeline status |
| `/help` | Display available commands |

### 10.3 Callback Actions

| Action | Description |
|--------|-------------|
| `approve_script` | Accept script, proceed to video generation |
| `reject_script` | Reject with optional feedback |
| `approve_video` | Accept video, proceed to publishing |
| `reject_video` | Reject video |
| `regenerate` | Re-run synthesis step |

---

## 11. Testing Infrastructure

### 11.1 Test Framework

| Component | Technology |
|-----------|------------|
| Framework | pytest |
| Async Support | pytest-asyncio |
| HTTP Testing | httpx (TestClient) |
| Mocking | unittest.mock, MagicMock |

### 11.2 Test Fixtures

| Fixture | Purpose |
|---------|---------|
| `event_loop` | Async test support (session-scoped) |
| `mock_supabase` | Database client mock |
| `mock_openai` | LLM response mock |
| `mock_heygen` | Video API mock |
| `mock_blotato` | Social posting mock |
| `mock_aggregator` | News source mock |

### 11.3 Test Suites

**API Tests:**
- Health endpoints (root, /health)
- Dashboard API (stats, summary)
- Briefings API (list, create, duplicate prevention)

**News Aggregator Tests:**
- RSS feed parsing
- Article extraction
- Deduplication logic
- Error handling

### 11.4 Running Tests

```
pytest backend/tests/                    # All tests
pytest backend/tests/test_api.py -v     # API tests only
pytest backend/tests/ -k "dashboard"    # Pattern matching
```

---

## 12. Deployment

### 12.1 Docker Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER DEPLOYMENT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │    Frontend     │      │     Backend     │                  │
│  │  (Nginx/React)  │ ──── │    (FastAPI)    │                  │
│  │   Port: 3000    │      │   Port: 8000    │                  │
│  └─────────────────┘      └─────────────────┘                  │
│           │                        │                            │
│           └────────────┬───────────┘                            │
│                        │                                        │
│                  maya-network                                   │
│                        │                                        │
│           ┌────────────┴────────────┐                          │
│           │      External APIs       │                          │
│           │  Supabase, HeyGen, etc. │                          │
│           └─────────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Environment Variables

**Required:**

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | GPT-4o access |
| `HEYGEN_API_KEY` | Video generation |
| `MAYA_AVATAR_ID` | Avatar selection |
| `MAYA_VOICE_ID` | Voice selection |
| `SUPABASE_URL` | Database endpoint |
| `SUPABASE_KEY` | Database authentication |
| `DATABASE_URL` | PostgreSQL connection string |

**Optional:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | false |
| `FRONTEND_URL` | React app URL | http://localhost:3000 |
| `BACKEND_URL` | API URL | http://localhost:8000 |
| `LANGCHAIN_TRACING_V2` | Enable observability | true |
| `LANGCHAIN_API_KEY` | LangSmith API key | - |
| `LANGCHAIN_PROJECT` | Project name | maya-weekly-news |
| `OPENAI_MODEL` | Model selection | gpt-4o |
| `BLOTATO_API_KEY` | Social posting | - |
| `BLOTATO_BASE_URL` | API endpoint | https://api.blotato.com/v1 |
| `TELEGRAM_API_ID` | Telegram news aggregation | - |
| `TELEGRAM_API_HASH` | Telegram auth | - |
| `SLACK_WEBHOOK_URL` | Slack notifications | - |
| `SLACK_CHANNEL` | Default channel | #maya-content |
| `TELEGRAM_BOT_TOKEN` | Bot notifications | - |
| `TELEGRAM_CHAT_ID` | Approval chat | - |
| `ADMIN_API_KEY` | Admin authentication | - |

### 12.3 Deployment Options

| Platform | Use Case |
|----------|----------|
| Railway | Recommended for simplicity |
| Render | Alternative PaaS |
| Fly.io | Edge deployment |
| Docker + VPS | Full control |
| Vercel (Frontend) | Static hosting |

---

## 13. Cost Analysis

### 13.1 Monthly Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| Database | Supabase Free | **$0** |
| Observability | LangSmith Free | **$0** |
| Video Generation | HeyGen Creator (Annual) | **$29** |
| Social Posting | Blotato | **~$15-30** |
| Compute | Railway/your server | **$10-20** |
| LLM Costs | GPT-4o (~4 briefings) | **~$6** |
| News Sources | Telegram + RSS + Nitter | **$0** |
| Twitter API | ~~$200~~ | **$0** |
| **TOTAL** | | **~$60-85/month** |

### 13.2 Cost Comparison

| Scenario | Daily Posting | Weekly Posting |
|----------|--------------|----------------|
| Videos/month | ~30 | 4 |
| HeyGen | $330+ | $29 |
| LLM costs | ~$45 | ~$6 |
| Twitter API | $200 | $0 |
| **TOTAL** | **~$575** | **~$65** |

**Savings: ~89% reduction**

---

## 14. Feature Summary

### 14.1 Implemented Features

#### Core Pipeline
- [x] Multi-source news aggregation (RSS, Nitter, Telegram)
- [x] AI-powered article categorization (local, business, AI/tech)
- [x] Context-aware script synthesis (3 segments)
- [x] Human-in-the-loop approval gates (script & video)
- [x] AI avatar video generation (HeyGen)
- [x] Multi-platform social publishing (Blotato)
- [x] Real-time status tracking (WebSocket)

#### On-Demand Features
- [x] Article-to-video generation from URL
- [x] Multi-language support (English, Bahasa Melayu)
- [x] Multi-platform targeting
- [x] Script editing capability
- [x] Job history and retry

#### Management Features
- [x] News source management (add/edit/delete/test)
- [x] Cron schedule management with presets
- [x] Integration testing (HeyGen, Blotato, OpenAI, Supabase)
- [x] Analytics dashboard (stats, trends, success rates)
- [x] Approval workflows (script & video)
- [x] Mock database mode for development

#### Notification Systems
- [x] Slack: Rich formatted messages with buttons
- [x] Telegram: Bot messages with inline keyboards
- [x] WebSocket: Real-time pipeline updates
- [x] Commands: /start, /status, /help

#### Security
- [x] Admin API key authentication for sensitive operations
- [x] Environment-based configuration
- [x] Non-sensitive config exposure only

---

## 15. Roadmap

### 15.1 Completed Milestones

| Milestone | Status |
|-----------|--------|
| Core LangGraph pipeline | Done |
| Supabase database integration | Done |
| HeyGen video generation | Done |
| Blotato social publishing | Done |
| Human approval gates | Done |
| Slack/Telegram notifications | Done |
| React frontend dashboard | Done |
| On-demand article-to-video | Done |
| Source management | Done |
| Schedule management | Done |
| Analytics dashboard | Done |
| Admin authentication | Done |
| Mock database mode | Done |
| Testing infrastructure | Done |

### 15.2 Future Enhancements

#### Short-term

| Feature | Description | Priority |
|---------|-------------|----------|
| Video Templates | Multiple video styles/backgrounds | High |
| Thumbnail Generation | Auto-generate video thumbnails | High |
| Email Notifications | Alternative to Slack/Telegram | Medium |
| Batch Processing | Process multiple articles at once | Medium |
| Video Editing | Basic trim/crop capabilities | Medium |

#### Medium-term

| Feature | Description | Priority |
|---------|-------------|----------|
| Multi-Avatar Support | Different avatars for different segments | Medium |
| A/B Testing | Test different scripts/styles | Medium |
| Performance Analytics | Engagement metrics from social platforms | Medium |
| Content Calendar | Visual schedule management | Medium |
| Team Collaboration | Multi-user approval workflows | Low |

#### Long-term

| Feature | Description | Priority |
|---------|-------------|----------|
| Custom Voice Cloning | Maya's unique voice | Low |
| Live Streaming | Real-time news broadcasts | Low |
| Mobile App | iOS/Android management app | Low |
| API Marketplace | Third-party integrations | Low |
| White-label Solution | Customizable for other brands | Low |

### 15.3 Technical Debt

| Item | Description |
|------|-------------|
| Test Coverage | Expand unit and integration tests |
| Error Handling | Improve error recovery in pipeline |
| Rate Limiting | Add API rate limiting |
| Caching | Add Redis caching layer |
| Logging | Structured logging improvements |
| Documentation | API documentation (OpenAPI/Swagger) |

---

## Quick Reference

### Key Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Frequency | Weekly | 89% cost savings |
| Video tier | HeyGen Unlimited Avatar | $29/mo vs $330 |
| Twitter API | Nitter (free) | Avoid $200/mo API cost |
| Social posting | Blotato | Already using |
| Database | Supabase Free | Sufficient for weekly |
| Observability | LangSmith Free | 5K traces enough |
| Frontend | React + Vite | Modern, fast DX |
| State | React Query | Server state management |

### Architecture Principles

1. **Cost-effective**: Prioritize free tiers and affordable options
2. **Human-in-the-loop**: Always require approval before publishing
3. **Modular**: Each component can be replaced independently
4. **Observable**: Full tracing of pipeline execution
5. **Testable**: Mock mode for development without external dependencies

---

*Last updated: January 2026*
