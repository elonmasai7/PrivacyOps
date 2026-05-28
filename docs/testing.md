# Testing Guide

## Testing Strategy

The current test suite focuses on acceptance-critical backend workflows and tenancy controls.

## Run Tests

```bash
pytest backend/tests -q
```

Frontend quality checks (non-interactive):

```bash
cd frontend
npm run ci:check
```

CI pipeline file: `.github/workflows/ci.yml`.

## Current Coverage

### Core user journey

- register user
- login and receive token
- create organization
- submit onboarding and receive readiness score

### Compliance workflows

- create processing activity
- upload evidence file
- generate report
- download report export
- workflow CRUD parity for vendors, incidents, DSR, policies, and tasks
- workflow export parity (`CSV`, `JSON`, `PDF`) for operational modules

### Security and tenancy

- cross-tenant access denied
- role-based denied action checks
- GitLab integration connect + sync scanning path (mocked)

## Test Runtime Design

- SQLite test database (`test_privacyops.db`) for isolated test runs.
- Automatic schema reset between tests.
- Temporary storage cleanup for uploads/exports.

## Recommended Next Coverage

- integration success/failure paths (mock GitHub API responses)
- audit log assertions for all high-risk writes
- file validation edge cases (size/type)
- report export content assertions
