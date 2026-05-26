# Multi-Tenant Model

## Tenancy Root

- `organizations` is the root tenant entity.
- Every user belongs to one or more organizations through `memberships`.

## Membership and Role Model

- `memberships` creates scoped identity for each tenant.
- Role enum governs allowed actions in each organization context.
- Same user can hold different roles in different organizations.

## Isolation Enforcement

### Request-time checks

- Protected routes call `require_org_membership`.
- Privileged routes also call `require_role`.

### Query-time checks

- Tenant data queries filter on `organization_id`.
- Writes bind created records to the current tenant.

## Tenant-owned Domains

- Assessments, evidence, processing activities, incidents, vendors, reports, integrations, tasks, notifications, trust center data, and audit logs.

## Data Leak Prevention Pattern

- Never trust client-provided ownership alone.
- Resolve tenant scope from route + authenticated user membership.
- Return `403` for any access outside permitted membership.

## Extension Guidance

When adding new modules:

1. Add `organization_id` in model.
2. Add membership check in every route.
3. Add role checks for sensitive writes.
4. Add audit logging for high-risk actions.
