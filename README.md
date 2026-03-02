# MT5 Trade Tracker

Production-oriented full-stack app to automatically sync MetaTrader 5 trades, calculate advanced analytics, and visualize performance.

## Folder Structure

- `backend/` FastAPI API, JWT auth, MT5 sync service, analytics engine, tests
- `frontend/` React + Vite UI (dashboard + analysis)
- `.github/workflows/ci.yml` CI/CD checks
- `docker-compose.yml` local full-stack environment
- `.env.example` environment variable template

## Features

- Automatic MT5 sync endpoint (`POST /api/trades/sync`) with connection error handling
- Dashboard: total trades, win rate, total P/L, average R:R, equity curve, daily/weekly/monthly breakdown
- Analysis: date/symbol/type filters, max drawdown, Sharpe ratio, CSV export
- JWT authentication (register/login)
- Trade tags and notes fields in data model for future UI extension
- Environment-driven secrets management

## Tech Stack

- Frontend: React + Vite + Chart.js
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL (SQLite default for local quick start)
- CI: GitHub Actions
- Deployment: Vercel (frontend) + Render/Railway/Fly.io (backend)

## Local Setup

1. Copy env file:

```bash
cp .env.example .env
```

2. Start PostgreSQL (optional but recommended):

```bash
docker compose up -d db
```

3. Run backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Run frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend

- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: secret for JWT signing (required)
- `JWT_ALGORITHM`: default `HS256`
- `JWT_EXPIRE_MINUTES`: token expiration window
- `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_PATH`: MT5 credentials/config (never commit these)

### Frontend

- `VITE_API_URL`: backend URL (e.g. `https://your-api.onrender.com`)

## MT5 Integration Notes

- Uses official `MetaTrader5` Python package when available and configured.
- If MT5 package is unavailable in local dev, service falls back to mock data to keep UI/test workflow functional.
- Sync failures return HTTP 503 and store sync state for observability.

## Deployment Guide

### Backend (Render/Railway/Fly.io)

- Point service root to `backend/`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Add environment variables from `.env.example`

### Frontend (Vercel)

- Root directory: `frontend/`
- Build command: `npm run build`
- Output directory: `dist`
- Set `VITE_API_URL` to deployed backend URL

## GitHub Secrets

Store deployment credentials and runtime secrets in GitHub repository secrets:

- `JWT_SECRET`
- `DATABASE_URL`
- `MT5_LOGIN`
- `MT5_PASSWORD`
- `MT5_SERVER`

## Scaling & Maintainability Notes

- Backend structure is modular (`routers`, `services`, `core`)
- Analytics pipeline isolated for testability
- API and UI are decoupled for easier iteration
- Add Redis + task queue for scheduled sync in next iteration
