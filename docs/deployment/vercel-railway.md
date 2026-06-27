# Vercel + Railway Deployment

## Backend: Railway

Deploy the repository root using the existing `railway.toml`. Railway should
build from `backend/Dockerfile` and start:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required Railway environment variables:

```text
FRONTEND_URL=https://<vercel-domain>
BACKEND_URL=https://<railway-domain>
SUPABASE_URL=<value>
SUPABASE_KEY=<value>
DATABASE_URL=<value>
OPENAI_API_KEY=<value>
OPENAI_MODEL=<value>
HEYGEN_API_KEY=<value>
MAYA_AVATAR_ID=<value>
MAYA_VOICE_ID=<value>
```

Optional integrations:

```text
LANGCHAIN_TRACING_V2=<value>
LANGCHAIN_API_KEY=<value>
LANGCHAIN_PROJECT=<value>
BLOTATO_API_KEY=<value>
BLOTATO_BASE_URL=<value>
TELEGRAM_BOT_TOKEN=<value>
TELEGRAM_CHAT_ID=<value>
TELEGRAM_API_ID=<value>
TELEGRAM_API_HASH=<value>
TELEGRAM_SESSION_NAME=<value>
SLACK_WEBHOOK_URL=<value>
SLACK_CHANNEL=<value>
```

Smoke test:

```bash
curl https://<railway-domain>/health
curl https://<railway-domain>/api/v1/settings/status
```

## Frontend: Vercel

Project settings:

```text
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

Required Vercel environment variables:

```text
VITE_API_BASE_URL=https://<railway-domain>/api/v1
VITE_WS_BASE_URL=wss://<railway-domain>/api/v1/ws
```

Enable Vercel Deployment Protection until app-level admin authentication is
implemented.

Smoke test:

```text
Open the Vercel URL.
Refresh a nested route such as /content.
Confirm dashboard API calls go to Railway without CORS errors.
Confirm WebSocket connections use the Railway wss:// URL.
```

Avoid triggering paid OpenAI, HeyGen, or publishing flows during deployment
smoke tests unless explicitly approved.
