# Architecture Documentation

![PrivacyOps Africa Core Architecture](assets/architecture-core.svg)

![PrivacyOps Africa Core Readiness Loop](assets/readiness-loop.svg)

## Overview

PrivacyOps Africa Core is implemented as a modular web application with a clear split between frontend UX and backend domain APIs.

- `frontend/` handles user workflows, module navigation, empty-state UX, and action forms.
- `backend/app/routers` handles API surfaces by bounded module.
- `backend/app/services.py` handles core business logic and helper operations.
- `backend/app/models.py` defines relational persistence.

## Application Architecture

### Runtime flow

1. User action starts in frontend workspace module (`/app/[orgId]/[module]`).
2. Frontend calls a scoped API route with bearer token (`frontend/lib/api.ts`).
3. Router validates payload, enforces membership and role checks.
4. Service layer executes module logic (scoring, exports, integrations, audit events).
5. SQLAlchemy persists changes to organization-scoped tables.
6. API returns structured JSON; frontend updates module state and UI.

### Architectural boundaries

- **Presentation boundary**: frontend components and module pages only orchestrate UX.
- **Policy boundary**: routers enforce authentication, authorization, and request validation.
- **Domain boundary**: services encapsulate business rules and external API interactions.
- **Persistence boundary**: models represent normalized domain records with tenant ownership.
- **Operations boundary**: CI, containerization, and deployment artifacts stay outside domain logic.

## Layered Backend Design

### Router Layer

- Validates request payloads via Pydantic schemas.
- Enforces authentication and authorization dependencies.
- Converts service output into API responses.

### Service Layer

- Trust Readiness Score computation.
- Readiness component breakdown.
- Audit event recording.
- Report export generation (`PDF`, `DOCX`, `CSV`, `JSON`).
- Integration fetch/scan helpers (GitHub, GitLab, AWS).

### Data Layer

- SQLAlchemy models for all tenancy, governance, and workflow entities.
- Organization ownership represented through `organization_id` on tenant data.
- Versioning entities for evidence and policies.

## Frontend Design

- Next.js app router with workspace route: `/app/[orgId]/[module]`.
- Shared shell component with module navigation.
- Module metadata registry (`frontend/lib/modules.ts`) to keep module UX wording structured.
- API abstraction in `frontend/lib/api.ts` with token propagation.

## Multi-Tenant Isolation in Runtime

- Membership checks run before all protected data access.
- Role checks restrict privileged actions (framework management, integrations, billing override).
- Audit events are recorded per tenant context.

## Security and Resilience Controls

- Password hashing with `pbkdf2_sha256`.
- JWT access-token authentication.
- RBAC enforcement at endpoint level.
- Rate-limiting middleware for abuse resistance.
- Security headers middleware (`CSP`, `HSTS`, `X-Frame-Options`, `nosniff`, `Referrer-Policy`).
- File upload size limits and SHA-256 hashing.

## Operational Components

- PostgreSQL as primary transactional store.
- Redis available for queue/cache expansion.
- Docker Compose orchestration for local and lower environments.
- CI pipeline for backend tests and frontend lint/typecheck/build gates.
