# Maya AI News Anchor

An automated AI-powered news anchor system for Southeast Asia. Maya aggregates news from multiple sources, synthesizes them into engaging scripts, generates videos using AI avatars, and publishes to social media platforms.

## Features

- **News Aggregation**: Collects news from RSS feeds, Telegram channels, and Twitter (via Nitter)
- **AI-Powered Synthesis**: Uses GPT-4 to create engaging news scripts with an Asian perspective
- **Video Generation**: Creates professional videos using HeyGen AI avatars
- **Multi-Platform Publishing**: Distributes to Instagram, TikTok, YouTube, and LinkedIn via Blotato
- **Human-in-the-Loop**: Approval gates for scripts and videos before publishing
- **Modern Dashboard**: React-based UI for monitoring and approvals

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MAYA WEEKLY NEWS ANCHOR PIPELINE                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                          │
│  │ Telegram │  │   RSS    │  │  Nitter  │  News Sources (FREE)     │
│  │ Channels │  │  Feeds   │  │ Scrapers │                          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                          │
│       └─────────────┴─────────────┘                                │
│                     │                                               │
│              ┌──────▼──────┐                                       │
│              │  LANGGRAPH  │  Multi-Agent Orchestration            │
│              │   PIPELINE  │                                       │
│              └──────┬──────┘                                       │
│                     │                                               │
│  [Aggregate] → [Dedupe] → [Categorize] → [Synthesize x3 segments] │
│                                               │                    │
│                               [Generate Scripts with Asian Twist]  │
│                                               │                    │
│                            ┌──────────────────▼───────────────┐   │
│                            │   HUMAN APPROVAL GATE #1         │   │
│                            │   Review scripts before video    │   │
│                            └──────────────────┬───────────────┘   │
│                                               │                    │
│                               [HeyGen Video Generation]           │
│                                               │                    │
│                            ┌──────────────────▼───────────────┐   │
│                            │   HUMAN APPROVAL GATE #2         │   │
│                            │   Review video + caption         │   │
│                            └──────────────────┬───────────────┘   │
│                                               │                    │
│                               [Blotato Multi-Platform Post]       │
└───────────────────────────────────────────────┼─────────────────────┘
                                                │
        ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
        │Instagram│  │ TikTok  │  │ YouTube │  │LinkedIn │
        └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional)

### 1. Clone and Setup

```bash
cd news_agent_maya

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
```

Required API keys:
- **OpenAI**: For LLM-powered script synthesis
- **HeyGen**: For AI video generation
- **Supabase**: For database

Optional:
- **Blotato**: For social media posting
- **Telegram API**: For news aggregation
- **Slack/Telegram Bot**: For notifications

### 3. Setup Database

Run the SQL schema in your Supabase project:

```bash
# Copy contents of database/schema.sql to Supabase SQL Editor
```

### 4. Run the Application

**Development mode:**

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**With Docker:**

```bash
docker-compose up --build
```

Access the dashboard at http://localhost:3000

## Project Structure

```
news_agent_maya/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes
│   │   ├── agents/        # LangGraph pipeline
│   │   ├── core/          # Configuration
│   │   ├── integrations/  # HeyGen, Blotato clients
│   │   ├── models/        # Pydantic schemas
│   │   └── services/      # Database, aggregation
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── lib/           # API client, utils
│   │   └── styles/        # Tailwind CSS
│   ├── package.json
│   └── Dockerfile
├── database/
│   └── schema.sql         # Supabase schema
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Briefings
- `POST /api/v1/briefings/` - Create new weekly briefing
- `GET /api/v1/briefings/` - List all briefings
- `GET /api/v1/briefings/{thread_id}` - Get briefing details
- `GET /api/v1/briefings/current` - Get current week's briefing

### Approvals
- `POST /api/v1/approvals/script` - Approve/reject scripts
- `POST /api/v1/approvals/video` - Approve/reject video
- `GET /api/v1/approvals/pending` - Get pending approvals

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/pipeline-status/{thread_id}` - Get pipeline status

### Settings
- `GET /api/v1/settings/status` - Get integration status
- `POST /api/v1/settings/test-connection` - Test service connections

## Deployment

### Railway (Recommended)

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy - Railway will use the `railway.toml` configuration

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Manual

Deploy the backend to any Python hosting (Railway, Render, Fly.io) and the frontend to static hosting (Vercel, Netlify).

## Cost Estimate

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| Database | Supabase Free | $0 |
| Observability | LangSmith Free | $0 |
| Video Generation | HeyGen Creator | $29 |
| Social Posting | Blotato | ~$15-30 |
| Compute | Railway/Render | $10-20 |
| LLM Costs | GPT-4o (~4 briefings) | ~$6 |
| News Sources | Telegram + RSS + Nitter | $0 |
| **Total** | | **~$60-85/month** |

## Weekly Schedule

Maya runs on a weekly schedule:
- **Sunday 6 AM UTC** (2 PM SGT): Automated pipeline trigger
- Aggregates past week's news
- Sends scripts for approval
- After approval, generates video
- After video approval, publishes to all platforms

## License

MIT License
