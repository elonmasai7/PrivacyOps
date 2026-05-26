import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership
from app.models import Integration, IntegrationProvider, User

router = APIRouter(prefix="/security-posture", tags=["security_posture"])


class AppCheckRequest(BaseModel):
    url: HttpUrl


@router.get("/{organization_id}/integrations-state")
def integrations_state(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    providers = {p.value for p in IntegrationProvider}
    existing = {
        row.provider.value: {
            "status": row.status,
            "last_synced_at": row.last_synced_at,
            "setup_instructions": f"Connect {row.provider.value} using API token or OAuth in Integrations page.",
        }
        for row in db.query(Integration).filter(Integration.organization_id == organization_id).all()
    }
    return {
        "integrations": [
            existing.get(
                provider,
                {
                    "provider": provider,
                    "status": "not_connected",
                    "setup_instructions": f"No connection found for {provider}. Use manual evidence workflow until connected.",
                },
            )
            for provider in sorted(providers)
        ]
    }


@router.post("/{organization_id}/application-check")
async def application_check(
    organization_id: str,
    payload: AppCheckRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)

    target = str(payload.url)
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(target)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach target URL: {exc}") from exc

    headers = {k.lower(): v for k, v in response.headers.items()}
    checks = {
        "https_status": target.startswith("https://"),
        "csp_present": "content-security-policy" in headers,
        "hsts_present": "strict-transport-security" in headers,
        "x_frame_options": headers.get("x-frame-options"),
        "referrer_policy": headers.get("referrer-policy"),
        "x_content_type_options": headers.get("x-content-type-options"),
        "set_cookie_flags": [h for h in response.headers.get_list("set-cookie")],
        "rate_limit_headers": {
            "limit": headers.get("x-ratelimit-limit"),
            "remaining": headers.get("x-ratelimit-remaining"),
            "reset": headers.get("x-ratelimit-reset"),
        },
    }

    warnings = []
    if not checks["https_status"]:
        warnings.append("HTTPS is not enforced")
    if not checks["csp_present"]:
        warnings.append("Missing Content-Security-Policy header")
    if not checks["hsts_present"]:
        warnings.append("Missing Strict-Transport-Security header")

    return {
        "url": target,
        "status_code": response.status_code,
        "checks": checks,
        "warnings": warnings,
    }
