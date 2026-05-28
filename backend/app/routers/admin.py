from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import BackgroundJob, FrameworkVersion, Integration, RoleName, SystemSetting, User
from app.services import write_audit_log

router = APIRouter(prefix="/admin", tags=["admin"])


class SystemSettingUpsertRequest(BaseModel):
    key: str = Field(min_length=2, max_length=120)
    value: str = Field(min_length=1, max_length=4000)


class BackgroundJobCreateRequest(BaseModel):
    job_type: str = Field(min_length=2, max_length=120)
    payload: dict = Field(default_factory=dict)


@router.get("/{organization_id}/settings")
def list_system_settings(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})
    records = db.query(SystemSetting).filter(SystemSetting.organization_id == organization_id).all()
    by_key = {record.key: record.value for record in records}
    if "ai_assistant_enabled" not in by_key:
        by_key["ai_assistant_enabled"] = "false"
    return by_key


@router.put("/{organization_id}/settings", status_code=status.HTTP_201_CREATED)
def upsert_system_setting(
    organization_id: str,
    payload: SystemSettingUpsertRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    existing = (
        db.query(SystemSetting)
        .filter(SystemSetting.organization_id == organization_id, SystemSetting.key == payload.key)
        .first()
    )
    if existing:
        existing.value = payload.value
        db.add(existing)
    else:
        existing = SystemSetting(organization_id=organization_id, key=payload.key, value=payload.value)
        db.add(existing)

    db.commit()

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="admin.system_setting_upserted",
        target_type="system_setting",
        target_id=existing.id,
        metadata={"key": payload.key},
    )

    return {"id": existing.id, "key": existing.key, "value": existing.value}


@router.post("/{organization_id}/jobs", status_code=status.HTTP_201_CREATED)
def create_background_job(
    organization_id: str,
    payload: BackgroundJobCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    job = BackgroundJob(
        organization_id=organization_id,
        job_type=payload.job_type,
        payload=payload.payload,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="admin.background_job_created",
        target_type="background_job",
        target_id=job.id,
        metadata={"job_type": payload.job_type},
    )

    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "created_at": job.created_at,
    }


@router.get("/{organization_id}/jobs")
def list_background_jobs(
    organization_id: str,
    only_failed: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    query = db.query(BackgroundJob).filter(BackgroundJob.organization_id == organization_id)
    if only_failed:
        query = query.filter(BackgroundJob.status == "failed")

    jobs = query.order_by(BackgroundJob.created_at.desc()).limit(100).all()
    return [
        {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        }
        for job in jobs
    ]


@router.patch("/{organization_id}/jobs/{job_id}/{job_status}")
def update_background_job_status(
    organization_id: str,
    job_id: str,
    job_status: str,
    error_message: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    if job_status not in {"queued", "running", "completed", "failed"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid job status")

    job = db.get(BackgroundJob, job_id)
    if not job or job.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background job not found")

    if job_status == "running" and not job.started_at:
        job.started_at = datetime.utcnow()
    if job_status in {"completed", "failed"}:
        job.finished_at = datetime.utcnow()

    job.status = job_status
    job.error_message = error_message
    db.add(job)
    db.commit()

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="admin.background_job_status_updated",
        target_type="background_job",
        target_id=job.id,
        metadata={"status": job_status},
    )
    return {"id": job.id, "status": job.status}


@router.get("/{organization_id}/system-health")
def get_system_health(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    integrations = db.query(Integration).filter(Integration.organization_id == organization_id).all()
    connected = len([row for row in integrations if row.status == "connected"])
    failed_jobs = (
        db.query(BackgroundJob)
        .filter(BackgroundJob.organization_id == organization_id, BackgroundJob.status == "failed")
        .count()
    )
    framework_versions = (
        db.query(FrameworkVersion)
        .order_by(FrameworkVersion.created_at.desc())
        .limit(200)
        .all()
    )
    reviewed = len([row for row in framework_versions if row.review_status in {"community-reviewed", "expert-reviewed"}])

    return {
        "database": "ok",
        "integrations_connected": connected,
        "integrations_total": len(integrations),
        "failed_jobs": failed_jobs,
        "framework_packs_reviewed": reviewed,
        "framework_packs_total": len(framework_versions),
    }


@router.get("/{organization_id}/integration-errors")
def list_integration_errors(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    errors = (
        db.query(Integration)
        .filter(Integration.organization_id == organization_id, Integration.last_error.is_not(None))
        .order_by(Integration.updated_at.desc())
        .all()
    )
    return [
        {
            "id": row.id,
            "provider": row.provider.value,
            "status": row.status,
            "last_error": row.last_error,
            "last_synced_at": row.last_synced_at,
        }
        for row in errors
    ]
