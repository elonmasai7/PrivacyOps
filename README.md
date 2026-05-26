# PrivacyOps Africa

PrivacyOps Africa is an Africa-first privacy, compliance, and security posture automation platform built for startups, SMEs, fintechs, healthtechs, edtechs, SaaS companies, NGOs, and enterprises operating across Kenya and broader African markets.

The platform helps organizations operationalize compliance readiness for:

- Kenya Data Protection Act (DPA)
- GDPR
- SOC 2 readiness
- ISO 27001 readiness

## Product Positioning

PrivacyOps Africa is not a certification authority and not legal counsel software.

- It helps organizations prepare evidence, controls, workflows, and governance outputs for audits and legal review.
- It never fabricates scans, legal obligations, reports, or evidence.
- It uses real organization data, real user actions, and real integrations where connected.

## Implemented Capabilities

### Workspace and Identity

- Real user registration and login (`/auth/register`, `/auth/login`)
- Token-based session model (`JWT`)
- Organization creation and multi-tenant memberships
- Role-based authorization model (owner/admin/compliance/security/auditor/member/viewer/trust guest/legal advisor)
- Organization-scoped audit logging

### Onboarding and Scoring

- Questionnaire-driven onboarding wizard
- Trust Readiness Score calculation from real onboarding responses
- Suggested frameworks, risk areas, and next actions
- Readiness breakdown endpoint for score explainability

### Compliance Operations Modules

- Framework registry with framework/version model
- Data inventory and RoPA activity management
- Evidence Vault with document upload, hash tracking, and version table
- DPIA workflow creation and risk scoring
- Incident and breach tracking workflow
- Data Subject Request intake workflow
- Vendor registry workflow
- Policy draft workflow with legal-review flags
- Task workflow
- Trust center pages/doc approvals

### Reports

- Report generation from stored organization records
- Export support for `PDF`, `DOCX`, `CSV`, and `JSON`
- Framework and scope metadata included in payload

### Security Posture and Integrations

- GitHub integration with real PAT validation against GitHub API
- GitHub sync with real findings (branch protection/public repos)
- Security posture endpoint for application header checks
- Connector states for non-connected providers with manual-workflow guidance

### Frontend

- Landing, pricing, register, login, onboarding pages
- Workspace router and role-aware module shell
- Working module UI flows for:
  - processing activities
  - evidence upload
  - report generation and export download
  - GitHub connect and sync findings

## Tech Stack

- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy
- Database: PostgreSQL (SQLite used in tests)
- Cache/queue-ready: Redis
- Reporting: ReportLab (PDF), python-docx (DOCX), CSV/JSON exports
- Deployment: Docker + Docker Compose

## Repository Layout

```text
backend/
  app/
    main.py
    models.py
    routers/
    services.py
  tests/
frontend/
  app/
  components/
  lib/
docs/
docker-compose.yml
```

## Quick Start (Docker)

1. Copy environment templates if needed.
2. Start services:

```bash
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

## Quick Start (Manual)

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

- Root: `.env.example`
- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

See full reference: `docs/environment-variables.md`.

## Test Suite

Run backend acceptance coverage:

```bash
pytest backend/tests -q
```

Current tests verify:

- registration/login
- organization onboarding score
- processing activity creation
- evidence upload
- report generation/export
- organization isolation + RBAC deny paths

## Documentation Index

- `docs/architecture.md`
- `docs/api.md`
- `docs/database-schema.md`
- `docs/security-model.md`
- `docs/multi-tenant-model.md`
- `docs/integration-setup-guide.md`
- `docs/compliance-framework-management.md`
- `docs/ai-assistant-guardrails.md`
- `docs/testing.md`
- `docs/deployment.md`
- `docs/production-checklist.md`

## Legal and Compliance Notices

- AI outputs are operational guidance only and may require legal review.
- This platform does not provide legal advice.
- This platform does not issue SOC 2 or ISO 27001 certifications.
- Legal page templates are drafts until approved by qualified counsel.
