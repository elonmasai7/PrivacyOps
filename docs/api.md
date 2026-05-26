# API Documentation

Base URL: `/` (for local default: `http://localhost:8000`)

OpenAPI and interactive docs:

- `/docs`
- `/openapi.json`

## Authentication Model

- Most endpoints require `Authorization: Bearer <token>`.
- Token is issued by `POST /auth/login`.
- Token subject maps to `users.id`.

## Core Identity and Tenancy

### Auth

- `POST /auth/register` - create user account
- `POST /auth/login` - obtain access token
- `GET /auth/me` - current authenticated user
- `POST /auth/mfa/setup/begin` - start TOTP setup for logged-in user
- `POST /auth/mfa/setup/confirm` - confirm TOTP enrollment
- `POST /auth/mfa/verify-login` - complete login challenge when MFA is required
- `GET /auth/oauth/providers` - list provider configuration status
- `GET /auth/oauth/google/start` - generate Google OAuth authorization URL
- `POST /auth/oauth/callback` - exchange OAuth code and log user in

### Organizations

- `POST /organizations` - create organization and owner membership
- `GET /organizations` - list organizations available to user
- `GET /organizations/{organization_id}/membership` - get caller membership role
- `POST /organizations/{organization_id}/onboarding` - submit onboarding answers
- `POST /organizations/{organization_id}/members` - invite existing user to org
- `GET /organizations/{organization_id}/members` - list organization members

## Compliance and Governance Endpoints

### Framework Registry

- `GET /frameworks`
- `POST /frameworks/{organization_id}`

### Data Inventory / RoPA

- `POST /processing-activities/{organization_id}`
- `GET /processing-activities/{organization_id}`

### Evidence Vault

- `POST /evidence/{organization_id}/upload` (multipart upload)
- `GET /evidence/{organization_id}`

### Reports

- `POST /reports/{organization_id}`
- `GET /reports/{organization_id}`
- `GET /reports/{organization_id}/{report_id}/export/{format}`

Supported `format`: `pdf`, `docx`, `csv`, `json`.

### Dashboard and Score Explainability

- `GET /dashboard/{organization_id}`
- `GET /readiness/{organization_id}`

## Security Posture and Integrations

### Integrations

- `POST /integrations/{organization_id}/connect` (GitHub currently supported)
- `POST /integrations/{organization_id}/github/sync`
- `POST /integrations/{organization_id}/aws/sync`
- `GET /integrations/{organization_id}`
- `GET /integrations/{organization_id}/findings`

### Security Posture

- `GET /security-posture/{organization_id}/integrations-state`
- `POST /security-posture/{organization_id}/application-check`

## Workflow APIs

### DPIA

- `POST /dpia/{organization_id}`
- `GET /dpia/{organization_id}`

### Incident, Vendor, DSR, Policy, Task

- `POST|GET /workflows/{organization_id}/incidents`
- `POST|GET /workflows/{organization_id}/vendors`
- `POST|GET /workflows/{organization_id}/dsr`
- `POST|GET /workflows/{organization_id}/policies`
- `POST|GET /workflows/{organization_id}/tasks`
- `PATCH /workflows/{organization_id}/tasks/{task_id}/status`

## Trust, Billing, and Audit

- `GET /audit-logs/{organization_id}`
- `POST|GET /trust-center/{organization_id}/pages`
- `POST /trust-center/{organization_id}/documents/{document_id}/approve`
- `GET /trust-center/public/{organization_id}`
- `GET /billing/{organization_id}`
- `POST /billing/{organization_id}/admin-override`
- `POST /billing/{organization_id}/checkout-session`
- `POST /billing/webhook`

## Public Endpoints

- `GET /public/health`
- `GET /public/legal-pages`
- `GET /public/legal-pages/{slug}`

## Error Behavior

- `401` for missing/invalid token
- `403` for no membership or insufficient role
- `404` for missing resources
- `409` for conflicts (e.g. duplicate slug)
- `422` for validation failures
- `429` for rate-limit blocks
