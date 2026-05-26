# Testing Guide

## Backend tests

Run:

```bash
pytest backend/tests -q
```

## Acceptance checks covered

- Real user registration and login
- Organization creation and onboarding score generation
- Processing activity creation
- Evidence upload
- Report generation and export
- Organization isolation and RBAC denial checks
