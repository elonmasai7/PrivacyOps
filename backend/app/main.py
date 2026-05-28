import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routers import (
    admin,
    assistant,
    audit,
    auth,
    billing,
    dashboard,
    dpia,
    evidence,
    frameworks,
    integrations,
    notifications,
    organizations,
    processing_activities,
    public,
    readiness,
    reports,
    security_posture,
    trust_center,
    workflows,
)

OPENAPI_TAGS = [
    {"name": "auth", "description": "User authentication, MFA, and OAuth flows."},
    {"name": "organizations", "description": "Organization lifecycle, onboarding, and memberships."},
    {"name": "frameworks", "description": "Framework registry and framework pack governance."},
    {"name": "processing_activities", "description": "Data inventory and RoPA processing activities."},
    {"name": "evidence", "description": "Evidence Vault uploads and listing."},
    {"name": "reports", "description": "Readiness report generation and export."},
    {"name": "integrations", "description": "External integration setup and sync operations."},
    {"name": "security_posture", "description": "Application and integration posture checks."},
    {"name": "dpia", "description": "DPIA creation and tracking."},
    {"name": "workflow-vendors", "description": "Vendor risk workflow API endpoints."},
    {"name": "workflow-incidents", "description": "Incident and breach workflow API endpoints."},
    {"name": "workflow-dsr", "description": "Data subject request workflow API endpoints."},
    {"name": "workflow-policies", "description": "Policy lifecycle workflow API endpoints."},
    {"name": "workflow-tasks", "description": "Task management workflow API endpoints."},
    {"name": "assistant", "description": "Optional AI assistant operations (disabled by default)."},
    {"name": "admin", "description": "Self-hosted admin operations and system controls."},
    {"name": "audit_logs", "description": "Audit trail retrieval endpoints."},
]

app = FastAPI(title=settings.app_name, openapi_tags=OPENAPI_TAGS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


REQUEST_LOG: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_COUNT = 120


@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = REQUEST_LOG[ip]

    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_COUNT:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    bucket.append(now)
    return await call_next(request)


app.include_router(public.router)
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(readiness.router)
app.include_router(frameworks.router)
app.include_router(admin.router)
app.include_router(processing_activities.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(integrations.router)
app.include_router(notifications.router)
app.include_router(security_posture.router)
app.include_router(dashboard.router)
app.include_router(dpia.router)
app.include_router(workflows.router)
app.include_router(assistant.router)
app.include_router(trust_center.router)
app.include_router(billing.router)
app.include_router(audit.router)
