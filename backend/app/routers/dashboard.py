from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership
from app.models import AuditLog, Evidence, Incident, Integration, Organization, ProcessingActivity, SecurityFinding, Task, User, Vendor

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{organization_id}")
def get_dashboard(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    org = db.get(Organization, organization_id)

    activities = db.query(ProcessingActivity).filter(ProcessingActivity.organization_id == organization_id).count()
    evidence_count = db.query(Evidence).filter(Evidence.organization_id == organization_id).count()
    open_findings = (
        db.query(SecurityFinding)
        .filter(SecurityFinding.organization_id == organization_id, SecurityFinding.status == "open")
        .count()
    )
    open_tasks = db.query(Task).filter(Task.organization_id == organization_id, Task.status != "done").count()
    incidents = db.query(Incident).filter(Incident.organization_id == organization_id).count()
    vendors = db.query(Vendor).filter(Vendor.organization_id == organization_id).count()
    integrations = db.query(Integration).filter(Integration.organization_id == organization_id).all()
    audits = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "organization": {
            "id": org.id,
            "name": org.name,
            "trust_readiness_score": org.trust_readiness_score,
            "privacy_health_map": org.privacy_health_map,
        },
        "framework_scores": {
            "kenya_dpa": org.trust_readiness_score,
            "gdpr": org.trust_readiness_score,
            "soc2": max(org.trust_readiness_score - 5, 0),
            "iso27001": max(org.trust_readiness_score - 8, 0),
        },
        "risk_heatline": {
            "open_findings": open_findings,
            "open_incidents": incidents,
            "missing_evidence": max(0, activities - evidence_count),
        },
        "activity": {
            "open_tasks": open_tasks,
            "processing_activities": activities,
            "evidence_count": evidence_count,
            "vendor_count": vendors,
            "integration_health": [
                {
                    "provider": integration.provider.value,
                    "status": integration.status,
                    "last_synced_at": integration.last_synced_at,
                }
                for integration in integrations
            ],
            "audit_log_summary": [
                {
                    "action": log.action,
                    "target_type": log.target_type,
                    "created_at": log.created_at,
                }
                for log in audits
            ],
        },
    }
