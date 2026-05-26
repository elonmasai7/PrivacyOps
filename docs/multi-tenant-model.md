# Multi-Tenant Model

## Tenant primitive

- `organizations` is the tenancy root.

## Access model

- `memberships` binds users to organizations with a role.
- Endpoints call membership checks before data access.
- Role checks enforce action permissions.

## Data isolation

- Tenant-owned tables include `organization_id`.
- Controllers only query records scoped by `organization_id`.
