# Environment Variable Guide

## Usage

- Backend template: `backend/.env.example`
- Frontend template: `frontend/.env.example`
- Root convenience template: `.env.example`

## Backend Variables

### Application

- `APP_NAME`: API display name.
- `APP_ENV`: environment marker (`development`, `staging`, `production`).
- `APP_HOST`: bind host.
- `APP_PORT`: bind port.

### Database and Auth

- `DATABASE_URL`: SQLAlchemy DSN for PostgreSQL (or SQLite for test/dev).
- `JWT_SECRET`: symmetric signing key for auth tokens (must be strong in production).
- `JWT_ALGORITHM`: token algorithm (default `HS256`).
- `JWT_EXPIRY_MINUTES`: token expiry window.

### CORS and Uploads

- `CORS_ORIGINS`: comma-separated frontend origins.
- `UPLOAD_DIR`: local upload path (replace with object storage in production).
- `MAX_UPLOAD_SIZE_MB`: upload hard limit.

### Integrations and Billing

- `GITHUB_API_BASE`: GitHub API base URL.
- `STRIPE_SECRET_KEY`: billing provider key (optional unless billing enabled).

## Frontend Variables

- `NEXT_PUBLIC_API_BASE_URL`: backend API base URL consumed by browser client.

## Production Recommendations

- Store secrets in a managed secret manager.
- Never commit real keys to source control.
- Rotate JWT and integration secrets on incident response or schedule.
