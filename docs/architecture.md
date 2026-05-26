# Architecture Documentation

## System layers

- `frontend/`: Next.js client application
- `backend/app/routers`: API route modules
- `backend/app/services.py`: core domain service helpers
- `backend/app/models.py`: relational data model

## Backend design

- Router layer handles request/response and dependency injection
- Service layer handles scoring, audit writes, exports, and integration sync logic
- Data layer uses SQLAlchemy models with strict organization scoping

## Multi-tenant isolation

- Each core record includes `organization_id`
- Every protected endpoint checks membership and role
- Audit logs are organization-scoped

## Security controls

- Password hashing (`bcrypt`)
- JWT authentication
- Role-based authorization
- Upload size limits + file hash
- Security headers middleware
- API rate limiter middleware
