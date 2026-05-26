from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership
from app.models import Assessment, Evidence, Incident, Integration, Organization, ProcessingActivity, SecurityFinding, User, Vendor

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("/{organization_id}")
def readiness_breakdown(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    controls_completed = db.query(Evidence).filter(Evidence.organization_id == organization_id).count()
    activities = db.query(ProcessingActivity).filter(ProcessingActivity.organization_id == organization_id).count()
    missing_evidence = max(0, activities - controls_completed)
    open_incidents = db.query(Incident).filter(Incident.organization_id == organization_id, Incident.status == "open").count()
    open_findings = db.query(SecurityFinding).filter(SecurityFinding.organization_id == organization_id, SecurityFinding.status == "open").count()
    connected_integrations = db.query(Integration).filter(Integration.organization_id == organization_id, Integration.status == "connected").count()
    vendor_count = db.query(Vendor).filter(Vendor.organization_id == organization_id).count()
    assessment_count = db.query(Assessment).filter(Assessment.organization_id == organization_id).count()

    components = {
        "completed_controls": min(30, controls_completed * 2),
        "evidence_freshness": max(0, 20 - (missing_evidence * 2)),
        "incident_impact": max(0, 15 - (open_incidents * 3)),
        "security_findings_impact": max(0, 15 - (open_findings * 2)),
        "automation_coverage": min(10, connected_integrations * 2),
        "vendor_governance": min(5, vendor_count),
        "assessment_depth": min(5, assessment_count),
    }
    computed_score = sum(components.values())
    explained = {
        "trust_readiness_score": org.trust_readiness_score,
        "computed_readiness_score": computed_score,
        "components": components,
        "explanation": [
            "Completed controls increase readiness.",
            "Missing evidence lowers evidence freshness.",
            "Open incidents and unresolved findings reduce confidence.",
            "Connected integrations improve automation coverage.",
        ],
        "control_confidence_level": "high" if computed_score >= 75 else "medium" if computed_score >= 45 else "low",
    }
    return explained
