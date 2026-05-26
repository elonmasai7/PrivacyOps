# Contribution Guide

## Branching and Change Scope

- Use a feature branch per unit of work.
- Keep pull requests focused and reviewable.
- Prefer small, composable commits.

## Engineering Standards

- Keep backend modular (`routers`, `services`, `models`).
- Enforce organization scoping for all tenant-owned entities.
- Add role checks for privileged actions.
- Add audit logging for security-sensitive mutations.

## Data and Integrity Rules

- Do not introduce seeded or fake production data.
- Do not fabricate API integrations or evidence records.
- Use empty states where real data is unavailable.

## Testing Expectations

- Add or update tests for changed behavior.
- Prioritize tests for auth, authorization, tenancy, evidence, and reporting.

## Documentation Expectations

- Update `README.md` and relevant files in `docs/` when behavior changes.
- Keep API documentation synchronized with route changes.
