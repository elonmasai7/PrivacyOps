# PrivacyOps Africa Core

PrivacyOps Africa Core is an open-source, self-hostable privacy, compliance, and security readiness platform built for African startups, SMEs, NGOs, and engineering teams.

![Architecture Overview](docs/assets/architecture-core.svg)

![Readiness Lifecycle](docs/assets/readiness-loop.svg)

It helps organizations operate practical readiness programs for:

- Kenya Data Protection Act (DPA)
- GDPR
- SOC 2 readiness
- ISO 27001 readiness

## Why this exists

Privacy and security tooling is often expensive, opaque, or designed for non-African regulatory realities. PrivacyOps Africa Core is designed to be inspectable, configurable, and community-maintained so local teams can run trustworthy readiness workflows with real data.

## Application architecture

- **Presentation layer**: Next.js workspace UI (`frontend/app`) with role-aware module navigation and real-data forms.
- **API layer**: FastAPI routers (`backend/app/routers`) expose module-bounded endpoints (auth, frameworks, workflows, reports, integrations, admin).
- **Service layer**: Core business logic (`backend/app/services.py`) handles readiness scoring, scanning integrations, report generation, and audit helpers.
- **Data layer**: SQLAlchemy domain models (`backend/app/models.py`) persist tenants, controls, evidence, workflows, findings, and logs in PostgreSQL.
- **Operations layer**: Docker Compose (`docker-compose.yml`), export/upload storage, and CI workflows (`.github/workflows/ci.yml`) support self-hosted delivery.

Full architecture and lifecycle visuals are in `docs/architecture.md`.

## What this project does

- Organization workspaces with RBAC, audit logs, onboarding, and readiness scoring.
- Framework registry with versioned framework packs and review status (`community-reviewed`, `expert-reviewed`, `unverified`).
- Data inventory (RoPA), DPIA workflow, DSR workflow, incident workflow, vendor workflow, policy workflow, evidence vault, tasks, and trust center foundations.
- Full CRUD/filter/export parity for DSR, incidents, vendors, policies, and tasks.
- Real report generation/export (`PDF`, `DOCX`, `CSV`, `JSON`) from organization data.
- Real integration connectors (GitHub, GitLab, AWS) with manual fallback workflow for unsupported providers.
- Optional AI assistant with guardrails, disabled by default, and organization-level opt-in via admin setting.
- Self-host deployment with Docker Compose.

## What this project does not do

- It does not provide legal advice.
- It does not replace a Data Protection Officer, lawyer, auditor, CPA, or certification body.
- It does not issue SOC 2 or ISO 27001 certifications.
- It does not auto-submit regulatory filings where no official API exists.
- It does not fabricate evidence, findings, controls, users, or reports.

## Open-source license choice

This repository uses **Apache-2.0** (`LICENSE`) to support broad adoption across startups, service providers, universities, consultants, and commercial deployments while preserving explicit patent grants and contribution clarity.

If the community later wants stricter network-use copyleft behavior, maintainers can discuss AGPL for future major versions through governance RFC.

## Stack

- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy
- Database: PostgreSQL (SQLite in tests)
- Queue/cache-ready: Redis
- Reports: ReportLab, python-docx, CSV/JSON exports
- Deploy: Docker + Docker Compose

## Repository layout

```text
backend/
  app/
  tests/
frontend/
  app/
  components/
  lib/
docs/
docker-compose.yml
```

## Quick start (Docker)

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

## Local development

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Detailed guide: `docs/local-development.md`.

## Environment variables

- Root: `.env.example`
- Backend: `backend/.env.example`
- Frontend: `frontend/.env.example`

Reference: `docs/environment-variables.md`.

## Framework packs

- Import framework pack: `POST /frameworks/{organization_id}/packs/import`
- Export framework pack: `GET /frameworks/{organization_id}/{framework_id}/packs/export`
- Update review state: `PATCH /frameworks/{organization_id}/versions/{version_id}/review`

Guide: `docs/framework-pack-guide.md`.

## Integrations

Implemented automated connectors:

- GitHub API
- GitLab API
- AWS APIs

Manual fallback guidance exists for providers without active connector support.

Guide: `docs/integration-setup-guide.md`.

## AI safety model

- AI module is disabled by default.
- Enable per organization with admin setting `ai_assistant_enabled=true`.
- Every response includes confidence and legal-review signaling.
- AI cannot mark controls complete or claim legal/certification outcomes.

Guide: `docs/ai-assistant-guardrails.md`.

## Testing

```bash
pytest backend/tests -q
```

Frontend CI-safe checks:

```bash
cd frontend
npm run ci:check
```

Repository CI pipeline is defined in `.github/workflows/ci.yml`.

Coverage includes auth/MFA/OAuth, RBAC and org isolation, onboarding scoring, framework pack workflows, evidence upload, reporting, integrations, and admin AI safety gating.

Guide: `docs/testing.md`.

## Documentation index

- Architecture: `docs/architecture.md`
- API: `docs/api.md`
- Workflow API examples:
  - `docs/api-workflow-vendors.md`
  - `docs/api-workflow-incidents.md`
  - `docs/api-workflow-dsr.md`
  - `docs/api-workflow-policies.md`
  - `docs/api-workflow-tasks.md`
- Database schema: `docs/database-schema.md`
- Integration setup: `docs/integration-setup-guide.md`
- Framework packs: `docs/framework-pack-guide.md`
- Deployment: `docs/deployment.md`
- Security model: `docs/security-model.md`
- Production hardening checklist: `docs/production-checklist.md`
- Requirements coverage matrix: `docs/requirement-coverage-matrix.md`

## Contributing and governance

- Contribution guide: `CONTRIBUTING.md`
- Governance model: `GOVERNANCE.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Security policy: `SECURITY.md`
- Roadmap: `ROADMAP.md`
- Changelog: `CHANGELOG.md`

## Legal disclaimer

PrivacyOps Africa Core supports operational readiness workflows. Users are responsible for validating legal and regulatory obligations with qualified professionals.
