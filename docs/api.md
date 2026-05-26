# API Documentation

Base URL: `/`

## Core endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /organizations`
- `GET /organizations`
- `POST /organizations/{organization_id}/onboarding`
- `POST /organizations/{organization_id}/members`

## Compliance workflows

- `GET|POST /frameworks`
- `POST /processing-activities/{organization_id}`
- `GET /processing-activities/{organization_id}`
- `POST /evidence/{organization_id}/upload`
- `GET /evidence/{organization_id}`
- `POST /reports/{organization_id}`
- `GET /reports/{organization_id}/{report_id}/export/{format}`

## Security posture and integrations

- `POST /integrations/{organization_id}/connect` (GitHub implemented)
- `POST /integrations/{organization_id}/github/sync`
- `GET /integrations/{organization_id}/findings`
- `POST /security-posture/{organization_id}/application-check`

## Other modules

- `/dpia`, `/workflows`, `/audit-logs`, `/trust-center`, `/billing`, `/assistant`, `/dashboard`, `/readiness`
