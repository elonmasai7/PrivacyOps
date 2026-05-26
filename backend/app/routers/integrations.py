from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Integration, IntegrationProvider, IntegrationToken, RoleName, SecurityFinding, User
from app.schemas import IntegrationConnectRequest, IntegrationResponse, SecurityFindingResponse
from app.services import scan_aws, scan_github, validate_aws_credentials, write_audit_log

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/{organization_id}/connect", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def connect_integration(
    organization_id: str,
    payload: IntegrationConnectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.security_manager})

    if payload.provider not in {IntegrationProvider.github.value, IntegrationProvider.aws.value}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Provider is not available for automated scan yet. "
                "Use manual evidence workflow until this connector is configured."
            ),
        )

    config = {}
    provider_enum = IntegrationProvider(payload.provider)
    token_ref = ""
    if payload.provider == IntegrationProvider.github.value:
        if not payload.personal_access_token:
            raise HTTPException(status_code=422, detail="personal_access_token is required")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {payload.personal_access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            test = await client.get(f"{settings.github_api_base}/user", headers=headers)
        if test.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub token validation failed")
        config = {"personal_access_token": payload.personal_access_token}
        token_ref = "github_pat"

    if payload.provider == IntegrationProvider.aws.value:
        if not payload.aws_access_key_id or not payload.aws_secret_access_key:
            raise HTTPException(
                status_code=422,
                detail="aws_access_key_id and aws_secret_access_key are required",
            )
        config = {
            "aws_access_key_id": payload.aws_access_key_id,
            "aws_secret_access_key": payload.aws_secret_access_key,
            "aws_session_token": payload.aws_session_token,
            "aws_region": payload.aws_region or settings.aws_region,
        }
        try:
            validate_aws_credentials(config)
        except Exception as exc:
            raise HTTPException(status_code=401, detail=f"AWS credential validation failed: {exc}") from exc
        token_ref = "aws_access_key"

    integration = (
        db.query(Integration)
        .filter(Integration.organization_id == organization_id, Integration.provider == provider_enum)
        .first()
    )
    if not integration:
        integration = Integration(
            organization_id=organization_id,
            provider=provider_enum,
            status="connected",
            config=config,
            last_synced_at=datetime.utcnow(),
        )
    else:
        integration.status = "connected"
        integration.config = config
        integration.last_synced_at = datetime.utcnow()
        integration.last_error = None
    db.add(integration)
    db.flush()

    token = IntegrationToken(integration_id=integration.id, token_ref=token_ref, scopes=[])
    db.add(token)
    db.commit()
    db.refresh(integration)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="integration.connected",
        target_type="integration",
        target_id=integration.id,
        metadata={"provider": payload.provider},
    )
    return integration


@router.post("/{organization_id}/github/sync", response_model=list[SecurityFindingResponse])
async def sync_github_findings(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.security_manager})

    integration = (
        db.query(Integration)
        .filter(Integration.organization_id == organization_id, Integration.provider == IntegrationProvider.github)
        .first()
    )
    if not integration or integration.status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected. Add a token first to run real checks.",
        )

    try:
        findings = await scan_github(integration, db)
    except httpx.HTTPStatusError as exc:
        integration.last_error = str(exc)
        integration.status = "error"
        db.add(integration)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub scan failed") from exc

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="integration.github_synced",
        target_type="integration",
        target_id=integration.id,
        metadata={"finding_count": len(findings)},
    )
    return findings


@router.post("/{organization_id}/aws/sync", response_model=list[SecurityFindingResponse])
async def sync_aws_findings(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.security_manager})

    integration = (
        db.query(Integration)
        .filter(Integration.organization_id == organization_id, Integration.provider == IntegrationProvider.aws)
        .first()
    )
    if not integration or integration.status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AWS is not connected. Add credentials first to run real checks.",
        )

    try:
        findings = scan_aws(integration, db)
    except Exception as exc:
        integration.last_error = str(exc)
        integration.status = "error"
        db.add(integration)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AWS scan failed") from exc

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="integration.aws_synced",
        target_type="integration",
        target_id=integration.id,
        metadata={"finding_count": len(findings)},
    )
    return findings


@router.get("/{organization_id}", response_model=list[IntegrationResponse])
def list_integrations(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return db.query(Integration).filter(Integration.organization_id == organization_id).all()


@router.get("/{organization_id}/findings", response_model=list[SecurityFindingResponse])
def list_findings(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return (
        db.query(SecurityFinding)
        .filter(SecurityFinding.organization_id == organization_id)
        .order_by(SecurityFinding.created_at.desc())
        .all()
    )
