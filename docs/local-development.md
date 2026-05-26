# Local Development Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or Docker)
- Redis 7+ (or Docker)

## Option A: Docker Compose (recommended)

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Option B: Manual Run

### 1) Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Set environment (example):

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/privacyops"
export JWT_SECRET="change-me"
export CORS_ORIGINS="http://localhost:3000"
```

Run backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2) Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

## First Functional Flow to Validate

1. Register real account.
2. Login.
3. Create organization.
4. Run onboarding and confirm Trust Readiness Score.
5. Add processing activity.
6. Upload evidence.
7. Generate report and download export.
