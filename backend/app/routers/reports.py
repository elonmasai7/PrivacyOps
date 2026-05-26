from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Evidence, Organization, ProcessingActivity, Report, ReportExport, RoleName, SecurityFinding, User
from app.schemas import ReportCreateRequest, ReportResponse
from app.services import generate_report_files, write_audit_log

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{organization_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    organization_id: str,
    payload: ReportCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.auditor})

    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    activities = db.query(ProcessingActivity).filter(ProcessingActivity.organization_id == organization_id).all()
    evidence = db.query(Evidence).filter(Evidence.organization_id == organization_id).all()
    findings = db.query(SecurityFinding).filter(SecurityFinding.organization_id == organization_id).all()

    completed_controls = len(evidence)
    failed_controls = len([f for f in findings if f.status == "open" and f.severity in {"high", "critical"}])
    missing_evidence_count = max(0, len(activities) - len(evidence))
    score = max(0, min(100, org.trust_readiness_score - (failed_controls * 5) - (missing_evidence_count * 3)))

    report_payload = {
        "organization": {
            "id": org.id,
            "name": org.name,
            "country": org.country,
        },
        "scope": payload.report_type,
        "framework": payload.framework,
        "score": score,
        "completed_controls": completed_controls,
        "failed_controls": failed_controls,
        "missing_evidence": missing_evidence_count,
        "risks": [finding.title for finding in findings[:20]],
        "recommended_remediation": [
            "Close high-severity security findings",
            "Attach evidence to uncovered controls",
            "Review risk ownership and deadlines",
        ],
        "evidence_references": [item.id for item in evidence],
        "generated_date": datetime.utcnow().isoformat(),
        "generated_by": user.full_name,
        "legal_disclaimer": "This report supports operational readiness and requires legal/compliance review.",
        "version_number": 1,
    }

    report = Report(
        organization_id=organization_id,
        framework=payload.framework,
        report_type=payload.report_type,
        score=score,
        payload=report_payload,
        generated_by_user_id=user.id,
    )
    db.add(report)
    db.flush()

    exports = generate_report_files(f"exports/{organization_id}", report.id, report_payload)
    for export_format, path in exports.items():
        db.add(ReportExport(report_id=report.id, export_format=export_format, file_path=path))

    db.commit()
    db.refresh(report)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="report.generated",
        target_type="report",
        target_id=report.id,
        metadata={"framework": payload.framework, "report_type": payload.report_type},
    )
    return report


@router.get("/{organization_id}", response_model=list[ReportResponse])
def list_reports(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return db.query(Report).filter(Report.organization_id == organization_id).order_by(Report.created_at.desc()).all()


@router.get("/{organization_id}/{report_id}/export/{export_format}")
def download_report_export(
    organization_id: str,
    report_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    export = (
        db.query(ReportExport)
        .join(Report, Report.id == ReportExport.report_id)
        .filter(
            Report.id == report_id,
            Report.organization_id == organization_id,
            ReportExport.export_format == export_format,
        )
        .first()
    )
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    return FileResponse(export.file_path)
