# Requirement Coverage Matrix

This matrix tracks implementation status against the full product specification.

Legend:

- `done`: implemented and testable now
- `partial`: foundation exists, but not complete for production requirement
- `missing`: not implemented yet

## Core platform

| Area | Status | Notes |
|---|---|---|
| Auth (email/password) | done | Register/login/me endpoints and UI are live |
| OAuth | done | Google OAuth start/callback flow implemented |
| MFA | done | TOTP setup + challenge verification implemented |
| Session management | partial | JWT-only; no refresh token rotation/revocation layer |
| Org workspace creation | done | Organization creation + owner membership |
| Team invitations | partial | Invite existing users only; no email invite flow |
| RBAC | partial | Role checks implemented, permission matrix not fully enforced |
| Audit logging | partial | Good coverage for major actions; not yet exhaustive |

## Frameworks and readiness

| Area | Status | Notes |
|---|---|---|
| Framework registry (versioned) | partial | Core models + pack import/export + review states available |
| Kenya DPA readiness | partial | Generic readiness + workflows; full legal control library pending |
| GDPR readiness | partial | Generic readiness + RoPA workflows; complete control content pending |
| SOC 2 readiness | partial | Report/readiness scaffolding; full TSC control engine pending |
| ISO 27001 readiness | partial | Report/readiness scaffolding; full ISMS toolkit pending |
| Scoring explainability | partial | Readiness breakdown endpoint exists; weights need governance tuning |

## Governance workflows

| Area | Status | Notes |
|---|---|---|
| Data inventory / RoPA | done | Create/list/update/delete + search/filter + export available |
| DPIA workflow | partial | Create/list + scoring exists; review/approval pipeline needs expansion |
| DSR workflow | done | Full CRUD/filter/export parity implemented |
| Incident and breach management | partial | Full CRUD/filter/export implemented; deeper breach-pack templates pending |
| Vendor risk management | partial | Full CRUD/filter/export implemented; questionnaire/scoring automation pending |
| Policy center | partial | Full CRUD/filter/export + versioning updates implemented; acknowledgement workflows incomplete |
| Task management | partial | Full CRUD/filter/export implemented; reminder automation pending |

## Evidence, reports, trust

| Area | Status | Notes |
|---|---|---|
| Evidence vault | partial | Upload/hash/version table implemented; malware scan and richer lifecycle pending |
| Reports engine | partial | Real exports implemented; full report templates by framework pending |
| Trust center | partial | Page/doc controls exist; NDA/request workflow not complete |

## Integrations and security posture

| Area | Status | Notes |
|---|---|---|
| GitHub integration | partial | Real connect + sync checks implemented; coverage should expand |
| GitLab/AWS integrations | partial | Real connect + sync for GitLab and AWS implemented |
| Google/MS/Cloudflare/etc | missing | Not implemented yet |
| App security header checks | done | URL-based header check endpoint implemented |
| Integration health dashboard | partial | Basic visibility exists |

## Billing, notifications, AI

| Area | Status | Notes |
|---|---|---|
| Billing (Stripe live) | partial | Billing state endpoint exists; live Stripe checkout/webhooks pending |
| Notifications | partial | In-app model exists; email/slack/teams/webhook delivery pending |
| AI assistant guardrails | partial | Structured guardrails + disabled-by-default org gating; provider abstraction still pending |

## Platform security and operations

| Area | Status | Notes |
|---|---|---|
| Input validation | done | Pydantic schemas on core routes |
| SQLi/XSS/CSRF baseline | partial | Framework-level baseline in place; full CSRF/session posture depends on auth model |
| Rate limiting | done | Middleware implemented |
| DDoS readiness | partial | App-level throttle present; infrastructure WAF policies pending |
| Secrets management | partial | Env-based now; managed secret integration pending |
| Monitoring/alerting | missing | No full observability stack wired yet |

## Frontend coverage

| Area | Status | Notes |
|---|---|---|
| Landing/pricing/auth/onboarding | done | Implemented |
| Workspace routing and module shell | done | Implemented |
| Working flows (activity/evidence/report/integration) | done | Implemented |
| Full module UX depth (all 40 requirements) | partial | Several modules still empty-state only |

## Test and documentation

| Area | Status | Notes |
|---|---|---|
| Acceptance tests | partial | Core tests exist; scope needs expansion |
| Architecture/API/docs | done | Detailed docs present |
| Runbooks | done | Incident/integration/audit runbooks added |

## Critical gaps to close first

1. Stronger session lifecycle (refresh/revocation) and account recovery workflows.
2. Complete framework control packs and deeper control-to-evidence mapping flows.
3. Expand integrations beyond GitHub and AWS (identity and cloud productivity providers next).
4. Notification delivery channels (email + Slack/webhook) with retries.
5. Observability stack: structured logs, error tracking, alerting, health SLOs.
6. Expand test coverage for tenancy edge cases, integrations, reports, and security controls.
