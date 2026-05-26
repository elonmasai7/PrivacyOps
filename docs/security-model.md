# Security Model

## Security Objectives

- Protect tenant boundaries.
- Enforce least-privilege access by role.
- Preserve evidence integrity.
- Maintain complete action traceability.

## Identity and Access

- Email/password authentication.
- Password hashing with `pbkdf2_sha256`.
- JWT-based session tokens.
- Role checks on privileged APIs.
- Membership checks on all tenant-scoped reads/writes.

## Multi-Tenant Data Protection

- `organization_id` scoping for tenant records.
- Endpoint-level organization membership validation.
- Forbidden responses for cross-tenant access attempts.

## API Security Controls

- Input validation with Pydantic schemas.
- Structured error handling by status class.
- Rate limiter middleware to reduce abuse bursts.
- Security headers middleware:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy`
  - `Content-Security-Policy`
  - `Strict-Transport-Security`

## File and Evidence Security

- File size limits (`MAX_UPLOAD_SIZE_MB`).
- SHA-256 file hashing for integrity tracking.
- Evidence version records.

## Auditability

- Central audit event writer in service layer.
- Captures actor, action, target type/id, and metadata.
- Supports regulatory and internal review trails.

## Integration Security Posture

- Real token validation for GitHub connection.
- Configured integration state stored by tenant.
- Sync failures captured with error state.

## Hardening Roadmap

- Add MFA challenge flow.
- Move tokens and files to encrypted managed storage.
- Add webhook signature verification for external callbacks.
- Add malware scanning for uploads.
