# PrivacyOps Africa

PrivacyOps Africa is an Africa-first privacy, compliance, and security posture automation platform for startups, SMEs, fintechs, healthtechs, edtechs, SaaS companies, NGOs, and enterprises.

## What is implemented

- Multi-tenant workspace model with organization-scoped data
- Authentication (email/password), JWT sessions, RBAC, audit logging
- Onboarding wizard with Trust Readiness Score
- Framework registry for Kenya DPA, GDPR, SOC 2 readiness, ISO 27001 readiness
- Data inventory / RoPA activities
- Evidence Vault with secure upload, hash capture, and version table
- Report engine with JSON, CSV, DOCX, and PDF exports
- Incident, DSR, vendor, task, policy, DPIA workflow APIs
- GitHub integration with real API token validation and real repository checks
- Trust center and legal template pages (marked for legal review)
- Frontend flows for auth, onboarding, workspace routing, and core module actions

## Stack

- Frontend: Next.js, TypeScript, Tailwind
- Backend: FastAPI, SQLAlchemy
- Database: PostgreSQL
- Queue/cache-ready: Redis
- Deployment: Docker Compose

## Local run (Docker)

```bash
docker compose up --build
```

Apps:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Local run (without Docker)

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment setup

- Copy `.env.example` to `.env` for local convenience.
- Use `backend/.env.example` and `frontend/.env.example` in deployment environments.

## Compliance caveats

- AI outputs are guidance only and include legal review labels for legal-risk content.
- The platform does not issue SOC 2 or ISO 27001 certification.
- Legal pages are draft templates and require counsel review before production launch.
