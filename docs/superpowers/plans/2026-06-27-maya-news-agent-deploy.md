# Maya News Agent Hybrid Deployment Plan

## Summary

Deploy the current GitHub version of Maya News Agent using a hybrid setup:
FastAPI backend on Railway, Vite frontend on Vercel.

The starting GitHub `main` commit is `03339d51f110df2e86d7b384d67321ce28b4f19d`.
This branch fixes deploy blockers only: backend import/test failures,
frontend build failures, and frontend runtime configuration for the Railway
backend.

## Implementation Checklist

- Back up the stale local checkout and clone GitHub fresh.
- Create branch `fix/maya-deploy-readiness`.
- Fix backend startup and test collection.
- Fix frontend TypeScript/API-contract build failures.
- Add frontend API/WebSocket environment configuration.
- Verify backend import/tests and frontend build/lint.
- Prepare Railway backend and Vercel frontend deployment handoff.

## Deployment Defaults

- Backend host: Railway.
- Frontend host: Vercel.
- Frontend project root: `frontend`.
- Frontend build command: `npm run build`.
- Frontend output directory: `dist`.
- Backend health check: `/health`.
- Frontend env:
  - `VITE_API_BASE_URL=https://<railway-domain>/api/v1`
  - `VITE_WS_BASE_URL=wss://<railway-domain>/api/v1/ws`

## Verification Commands

```bash
cd backend
python -B -m py_compile app/core/languages.py
python -B -c "import app.main"
pytest -q -p no:cacheprovider

cd ../frontend
npm install
npm run build
npm run lint
```
