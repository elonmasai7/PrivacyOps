# Security Model

- Authentication: email/password with hashed passwords (`bcrypt`)
- Authorization: RBAC with organization membership checks
- Tenant isolation: organization-scoped query guards
- Upload controls: file size cap and SHA-256 hashing
- Transport hardening: security headers middleware
- Abuse controls: rate limiting middleware
- Auditability: immutable audit log records for sensitive actions
