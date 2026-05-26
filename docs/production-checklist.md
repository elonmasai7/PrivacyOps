# Production Checklist

## Security and Access

- [ ] Strong `JWT_SECRET` configured and rotated policy defined.
- [ ] CORS restricted to approved production frontend origin(s).
- [ ] TLS termination enforced end-to-end.
- [ ] Role and permission model reviewed for least privilege.

## Data and Storage

- [ ] PostgreSQL backup and restore drills completed.
- [ ] Object storage configured for evidence/report artifacts.
- [ ] Data retention windows configured and documented.
- [ ] User/org deletion workflows tested.

## Platform Operations

- [ ] Health checks integrated with monitoring.
- [ ] Structured logging aggregation enabled.
- [ ] Error tracking configured (Sentry or equivalent).
- [ ] Alerting configured for integration failures and abnormal traffic.

## Billing and Integrations

- [ ] Stripe keys configured and webhook handling verified.
- [ ] GitHub token governance and least-privilege policy documented.
- [ ] Integration failure runbook prepared.

## Legal and Compliance

- [ ] Legal templates reviewed and approved by counsel.
- [ ] AI legal-review labels validated in assistant outputs.
- [ ] SOC 2 / ISO 27001 readiness disclaimers confirmed.

## Final Validation

- [ ] Register -> onboarding -> evidence -> report flow tested on production-like environment.
- [ ] Tenant isolation checks completed.
- [ ] Audit log integrity validated for sensitive actions.
