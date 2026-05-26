# Deployment Guide

## Deployment Model

Current repository supports container-based deployment with separate services:

- frontend
- backend
- PostgreSQL
- Redis

Use `docker-compose.yml` for local and staging. For production, use managed infrastructure equivalents.

## Container Deployment Steps

```bash
docker compose build
docker compose up -d
```

Validate health:

- `GET /public/health`
- frontend landing page loads

## Production-Grade Infrastructure Recommendations

- Managed PostgreSQL with backups and point-in-time recovery.
- Managed Redis or queue equivalent.
- Object storage for uploads and report exports.
- TLS termination via ingress/load balancer.
- WAF and DDoS protections (Cloudflare-compatible setup).
- Centralized logging and monitoring stack.
- Error tracking (Sentry or equivalent).

## Secrets and Config

- Keep all secrets in a secret manager.
- Do not bake secrets into images.
- Restrict integration tokens to least privilege.
- Rotate credentials periodically.

## Rollout Strategy

- Deploy to staging first.
- Run backend tests and smoke tests.
- Validate org onboarding, evidence upload, report generation, and integration sync.
- Promote to production only after security and legal checks pass.
