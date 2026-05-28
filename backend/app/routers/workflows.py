import csv
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import (
    DataSubjectRequest,
    Incident,
    Policy,
    PolicyVersion,
    RoleName,
    Task,
    User,
    Vendor,
)
from app.services import ensure_dir, write_audit_log

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _safe_sort(sort_by: str, allowed: dict[str, object], sort_order: str):
    column = allowed.get(sort_by)
    if column is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid sort field")
    return desc(column) if sort_order == "desc" else asc(column)


def _ensure_org_row(row, organization_id: str, label: str):
    if not row or row.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")


def _vendor_payload(row: Vendor) -> dict:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "name": row.name,
        "service_provided": row.service_provided,
        "data_processed": row.data_processed,
        "country": row.country,
        "subprocessors": row.subprocessors,
        "contract_status": row.contract_status,
        "dpa_status": row.dpa_status,
        "security_review_status": row.security_review_status,
        "risk_level": row.risk_level,
        "renewal_date": _iso(row.renewal_date),
        "owner_user_id": row.owner_user_id,
        "notes": row.notes,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _incident_payload(row: Incident) -> dict:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "title": row.title,
        "severity": row.severity,
        "affected_systems": row.affected_systems,
        "affected_data_subjects": row.affected_data_subjects,
        "affected_data_categories": row.affected_data_categories,
        "timeline": row.timeline,
        "root_cause": row.root_cause,
        "risk_of_harm": row.risk_of_harm,
        "status": row.status,
        "breach_clock_started_at": _iso(row.breach_clock_started_at),
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _dsr_payload(row: DataSubjectRequest) -> dict:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "request_type": row.request_type,
        "requester_email": row.requester_email,
        "identity_verified": row.identity_verified,
        "due_date": _iso(row.due_date),
        "assigned_owner_user_id": row.assigned_owner_user_id,
        "internal_notes": row.internal_notes,
        "completion_status": row.completion_status,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _policy_payload(row: Policy) -> dict:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "name": row.name,
        "owner_user_id": row.owner_user_id,
        "status": row.status.value,
        "effective_date": _iso(row.effective_date),
        "review_date": _iso(row.review_date),
        "visibility": row.visibility,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _task_payload(row: Task) -> dict:
    return {
        "id": row.id,
        "organization_id": row.organization_id,
        "title": row.title,
        "description": row.description,
        "assignee_user_id": row.assignee_user_id,
        "due_date": _iso(row.due_date),
        "priority": row.priority,
        "status": row.status,
        "framework_id": row.framework_id,
        "control_id": row.control_id,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _export_records(organization_id: str, module_slug: str, export_format: str, rows: list[dict]) -> FileResponse:
    normalized = export_format.lower()
    if normalized not in {"json", "csv", "pdf"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported export format")

    export_dir = Path(ensure_dir(f"exports/{organization_id}/workflows"))
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    base = export_dir / f"{module_slug}-{stamp}"

    if normalized == "json":
        file_path = base.with_suffix(".json")
        file_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return FileResponse(str(file_path), media_type="application/json", filename=file_path.name)

    if normalized == "csv":
        file_path = base.with_suffix(".csv")
        headers = sorted({key for row in rows for key in row.keys()})
        with file_path.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value) if isinstance(value, (list, dict)) else value for key, value in row.items()})
        return FileResponse(str(file_path), media_type="text/csv", filename=file_path.name)

    file_path = base.with_suffix(".pdf")
    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    y = 800
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, f"PrivacyOps Africa Core - {module_slug} export")
    y -= 24
    pdf.setFont("Helvetica", 9)
    for row in rows:
        line = json.dumps(row, ensure_ascii=True)
        pdf.drawString(40, y, line[:120])
        y -= 14
        if y < 80:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            y = 800
    pdf.save()
    return FileResponse(str(file_path), media_type="application/pdf", filename=file_path.name)


class VendorCreate(BaseModel):
    name: str
    service_provided: str
    data_processed: str
    country: str
    subprocessors: list[str] = Field(default_factory=list)
    contract_status: str
    dpa_status: str
    security_review_status: str
    risk_level: str
    renewal_date: datetime | None = None
    notes: str | None = None


class VendorUpdate(BaseModel):
    name: str | None = None
    service_provided: str | None = None
    data_processed: str | None = None
    country: str | None = None
    subprocessors: list[str] | None = None
    contract_status: str | None = None
    dpa_status: str | None = None
    security_review_status: str | None = None
    risk_level: str | None = None
    renewal_date: datetime | None = None
    notes: str | None = None


class IncidentCreate(BaseModel):
    title: str
    severity: str
    affected_systems: list[str]
    affected_data_subjects: int | None = None
    affected_data_categories: list[str]
    root_cause: str | None = None
    risk_of_harm: str | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    severity: str | None = None
    affected_systems: list[str] | None = None
    affected_data_subjects: int | None = None
    affected_data_categories: list[str] | None = None
    timeline: dict | None = None
    root_cause: str | None = None
    risk_of_harm: str | None = None
    status: str | None = None


class DSRCreate(BaseModel):
    request_type: str
    requester_email: str
    due_date: datetime | None = None
    internal_notes: str | None = None


class DSRUpdate(BaseModel):
    request_type: str | None = None
    requester_email: str | None = None
    identity_verified: bool | None = None
    due_date: datetime | None = None
    assigned_owner_user_id: str | None = None
    internal_notes: str | None = None
    completion_status: str | None = None


class PolicyCreate(BaseModel):
    name: str
    body_markdown: str


class PolicyUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    effective_date: datetime | None = None
    review_date: datetime | None = None
    visibility: str | None = None
    body_markdown: str | None = None
    is_ai_draft: bool = False
    requires_legal_review: bool = True


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    priority: str = "medium"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    priority: str | None = None
    status: str | None = None
    assignee_user_id: str | None = None
    framework_id: str | None = None
    control_id: str | None = None


@router.post("/{organization_id}/vendors", status_code=status.HTTP_201_CREATED, tags=["workflow-vendors"])
def create_vendor(
    organization_id: str,
    payload: VendorCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    vendor = Vendor(organization_id=organization_id, owner_user_id=user.id, **payload.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="vendor.created", target_type="vendor", target_id=vendor.id)
    return _vendor_payload(vendor)


@router.get("/{organization_id}/vendors", tags=["workflow-vendors"])
def list_vendors(
    organization_id: str,
    query: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    contract_status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    records = db.query(Vendor).filter(Vendor.organization_id == organization_id)
    if query:
        records = records.filter(Vendor.name.ilike(f"%{query}%"))
    if risk_level:
        records = records.filter(Vendor.risk_level == risk_level)
    if contract_status:
        records = records.filter(Vendor.contract_status == contract_status)
    records = records.order_by(_safe_sort(sort_by, {"name": Vendor.name, "renewal_date": Vendor.renewal_date, "created_at": Vendor.created_at}, sort_order)).offset(offset).limit(limit).all()
    return [_vendor_payload(row) for row in records]


@router.patch("/{organization_id}/vendors/{vendor_id}", tags=["workflow-vendors"])
def update_vendor(
    organization_id: str,
    vendor_id: str,
    payload: VendorUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    vendor = db.get(Vendor, vendor_id)
    _ensure_org_row(vendor, organization_id, "Vendor")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(vendor, key, value)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="vendor.updated", target_type="vendor", target_id=vendor.id)
    return _vendor_payload(vendor)


@router.delete("/{organization_id}/vendors/{vendor_id}", tags=["workflow-vendors"])
def delete_vendor(
    organization_id: str,
    vendor_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    vendor = db.get(Vendor, vendor_id)
    _ensure_org_row(vendor, organization_id, "Vendor")
    db.delete(vendor)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="vendor.deleted", target_type="vendor", target_id=vendor_id)
    return {"deleted": True}


@router.get("/{organization_id}/vendors/export/{export_format}", tags=["workflow-vendors"])
def export_vendors(
    organization_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    rows = db.query(Vendor).filter(Vendor.organization_id == organization_id).order_by(Vendor.created_at.desc()).all()
    payload = [
        {
            "id": row.id,
            "name": row.name,
            "service_provided": row.service_provided,
            "data_processed": row.data_processed,
            "country": row.country,
            "subprocessors": row.subprocessors,
            "contract_status": row.contract_status,
            "dpa_status": row.dpa_status,
            "security_review_status": row.security_review_status,
            "risk_level": row.risk_level,
            "renewal_date": _iso(row.renewal_date),
            "notes": row.notes,
        }
        for row in rows
    ]
    return _export_records(organization_id, "vendors", export_format, payload)


@router.post("/{organization_id}/incidents", status_code=status.HTTP_201_CREATED, tags=["workflow-incidents"])
def create_incident(
    organization_id: str,
    payload: IncidentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.security_manager})
    incident = Incident(
        organization_id=organization_id,
        title=payload.title,
        severity=payload.severity,
        affected_systems=payload.affected_systems,
        affected_data_subjects=payload.affected_data_subjects,
        affected_data_categories=payload.affected_data_categories,
        timeline={"created_at": datetime.utcnow().isoformat()},
        root_cause=payload.root_cause,
        risk_of_harm=payload.risk_of_harm,
        breach_clock_started_at=datetime.utcnow(),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="incident.created", target_type="incident", target_id=incident.id)
    return _incident_payload(incident)


@router.get("/{organization_id}/incidents", tags=["workflow-incidents"])
def list_incidents(
    organization_id: str,
    query: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    records = db.query(Incident).filter(Incident.organization_id == organization_id)
    if query:
        records = records.filter(Incident.title.ilike(f"%{query}%"))
    if severity:
        records = records.filter(Incident.severity == severity)
    if status_value:
        records = records.filter(Incident.status == status_value)
    rows = records.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    return [_incident_payload(row) for row in rows]


@router.patch("/{organization_id}/incidents/{incident_id}", tags=["workflow-incidents"])
def update_incident(
    organization_id: str,
    incident_id: str,
    payload: IncidentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.security_manager})
    incident = db.get(Incident, incident_id)
    _ensure_org_row(incident, organization_id, "Incident")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, key, value)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="incident.updated", target_type="incident", target_id=incident.id)
    return _incident_payload(incident)


@router.delete("/{organization_id}/incidents/{incident_id}", tags=["workflow-incidents"])
def delete_incident(
    organization_id: str,
    incident_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.security_manager})
    incident = db.get(Incident, incident_id)
    _ensure_org_row(incident, organization_id, "Incident")
    db.delete(incident)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="incident.deleted", target_type="incident", target_id=incident_id)
    return {"deleted": True}


@router.get("/{organization_id}/incidents/export/{export_format}", tags=["workflow-incidents"])
def export_incidents(
    organization_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    rows = db.query(Incident).filter(Incident.organization_id == organization_id).order_by(Incident.created_at.desc()).all()
    payload = [
        {
            "id": row.id,
            "title": row.title,
            "severity": row.severity,
            "affected_systems": row.affected_systems,
            "affected_data_subjects": row.affected_data_subjects,
            "affected_data_categories": row.affected_data_categories,
            "timeline": row.timeline,
            "root_cause": row.root_cause,
            "risk_of_harm": row.risk_of_harm,
            "status": row.status,
            "breach_clock_started_at": _iso(row.breach_clock_started_at),
        }
        for row in rows
    ]
    return _export_records(organization_id, "incidents", export_format, payload)


@router.post("/{organization_id}/dsr", status_code=status.HTTP_201_CREATED, tags=["workflow-dsr"])
def create_dsr(
    organization_id: str,
    payload: DSRCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    dsr = DataSubjectRequest(organization_id=organization_id, assigned_owner_user_id=user.id, **payload.model_dump())
    db.add(dsr)
    db.commit()
    db.refresh(dsr)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="dsr.created", target_type="data_subject_request", target_id=dsr.id)
    return _dsr_payload(dsr)


@router.get("/{organization_id}/dsr", tags=["workflow-dsr"])
def list_dsr(
    organization_id: str,
    request_type: str | None = Query(default=None),
    completion_status: str | None = Query(default=None),
    identity_verified: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    records = db.query(DataSubjectRequest).filter(DataSubjectRequest.organization_id == organization_id)
    if request_type:
        records = records.filter(DataSubjectRequest.request_type == request_type)
    if completion_status:
        records = records.filter(DataSubjectRequest.completion_status == completion_status)
    if identity_verified is not None:
        records = records.filter(DataSubjectRequest.identity_verified == identity_verified)
    rows = records.order_by(DataSubjectRequest.created_at.desc()).offset(offset).limit(limit).all()
    return [_dsr_payload(row) for row in rows]


@router.patch("/{organization_id}/dsr/{dsr_id}", tags=["workflow-dsr"])
def update_dsr(
    organization_id: str,
    dsr_id: str,
    payload: DSRUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    dsr = db.get(DataSubjectRequest, dsr_id)
    _ensure_org_row(dsr, organization_id, "Data subject request")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(dsr, key, value)
    db.add(dsr)
    db.commit()
    db.refresh(dsr)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="dsr.updated", target_type="data_subject_request", target_id=dsr.id)
    return _dsr_payload(dsr)


@router.delete("/{organization_id}/dsr/{dsr_id}", tags=["workflow-dsr"])
def delete_dsr(
    organization_id: str,
    dsr_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    dsr = db.get(DataSubjectRequest, dsr_id)
    _ensure_org_row(dsr, organization_id, "Data subject request")
    db.delete(dsr)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="dsr.deleted", target_type="data_subject_request", target_id=dsr_id)
    return {"deleted": True}


@router.get("/{organization_id}/dsr/export/{export_format}", tags=["workflow-dsr"])
def export_dsr(
    organization_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    rows = db.query(DataSubjectRequest).filter(DataSubjectRequest.organization_id == organization_id).order_by(DataSubjectRequest.created_at.desc()).all()
    payload = [
        {
            "id": row.id,
            "request_type": row.request_type,
            "requester_email": row.requester_email,
            "identity_verified": row.identity_verified,
            "due_date": _iso(row.due_date),
            "assigned_owner_user_id": row.assigned_owner_user_id,
            "internal_notes": row.internal_notes,
            "completion_status": row.completion_status,
        }
        for row in rows
    ]
    return _export_records(organization_id, "dsr", export_format, payload)


@router.post("/{organization_id}/policies", status_code=status.HTTP_201_CREATED, tags=["workflow-policies"])
def create_policy(
    organization_id: str,
    payload: PolicyCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.legal_advisor})
    policy = Policy(organization_id=organization_id, name=payload.name, owner_user_id=user.id)
    db.add(policy)
    db.flush()
    version = PolicyVersion(
        policy_id=policy.id,
        version_label="v1",
        body_markdown=payload.body_markdown,
        is_ai_draft=True,
        requires_legal_review=True,
        created_by_user_id=user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(policy)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="policy.created", target_type="policy", target_id=policy.id)
    return {"id": policy.id, "name": policy.name, "status": policy.status, "requires_legal_review": True}


@router.get("/{organization_id}/policies", tags=["workflow-policies"])
def list_policies(
    organization_id: str,
    status_value: str | None = Query(default=None, alias="status"),
    visibility: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    records = db.query(Policy).filter(Policy.organization_id == organization_id)
    if status_value:
        records = records.filter(Policy.status == status_value)
    if visibility:
        records = records.filter(Policy.visibility == visibility)
    rows = records.order_by(Policy.created_at.desc()).offset(offset).limit(limit).all()
    return [_policy_payload(row) for row in rows]


@router.patch("/{organization_id}/policies/{policy_id}", tags=["workflow-policies"])
def update_policy(
    organization_id: str,
    policy_id: str,
    payload: PolicyUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.legal_advisor})
    policy = db.get(Policy, policy_id)
    _ensure_org_row(policy, organization_id, "Policy")

    update_data = payload.model_dump(exclude_unset=True)
    body_markdown = update_data.pop("body_markdown", None)
    for key, value in update_data.items():
        if key in {"status", "visibility"} and value is None:
            continue
        setattr(policy, key, value)
    db.add(policy)

    if body_markdown is not None:
        latest = db.query(PolicyVersion).filter(PolicyVersion.policy_id == policy.id).order_by(PolicyVersion.created_at.desc()).first()
        next_version = 1
        if latest and latest.version_label.startswith("v"):
            try:
                next_version = int(latest.version_label.removeprefix("v")) + 1
            except ValueError:
                next_version = 1
        db.add(
            PolicyVersion(
                policy_id=policy.id,
                version_label=f"v{next_version}",
                body_markdown=body_markdown,
                is_ai_draft=payload.is_ai_draft,
                requires_legal_review=payload.requires_legal_review,
                created_by_user_id=user.id,
            )
        )

    db.commit()
    db.refresh(policy)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="policy.updated", target_type="policy", target_id=policy.id)
    return _policy_payload(policy)


@router.delete("/{organization_id}/policies/{policy_id}", tags=["workflow-policies"])
def delete_policy(
    organization_id: str,
    policy_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.legal_advisor})
    policy = db.get(Policy, policy_id)
    _ensure_org_row(policy, organization_id, "Policy")
    db.delete(policy)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="policy.deleted", target_type="policy", target_id=policy_id)
    return {"deleted": True}


@router.get("/{organization_id}/policies/export/{export_format}", tags=["workflow-policies"])
def export_policies(
    organization_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    rows = db.query(Policy).filter(Policy.organization_id == organization_id).order_by(Policy.created_at.desc()).all()
    payload = [
        {
            "id": row.id,
            "name": row.name,
            "owner_user_id": row.owner_user_id,
            "status": row.status.value,
            "effective_date": _iso(row.effective_date),
            "review_date": _iso(row.review_date),
            "visibility": row.visibility,
        }
        for row in rows
    ]
    return _export_records(organization_id, "policies", export_format, payload)


@router.post("/{organization_id}/tasks", status_code=status.HTTP_201_CREATED, tags=["workflow-tasks"])
def create_task(
    organization_id: str,
    payload: TaskCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.security_manager})
    task = Task(
        organization_id=organization_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority,
        assignee_user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="task.created", target_type="task", target_id=task.id)
    return _task_payload(task)


@router.get("/{organization_id}/tasks", tags=["workflow-tasks"])
def list_tasks(
    organization_id: str,
    query: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assignee_user_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    records = db.query(Task).filter(Task.organization_id == organization_id)
    if query:
        records = records.filter(Task.title.ilike(f"%{query}%"))
    if status_value:
        records = records.filter(Task.status == status_value)
    if priority:
        records = records.filter(Task.priority == priority)
    if assignee_user_id:
        records = records.filter(Task.assignee_user_id == assignee_user_id)
    rows = records.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
    return [_task_payload(row) for row in rows]


@router.patch("/{organization_id}/tasks/{task_id}", tags=["workflow-tasks"])
def update_task(
    organization_id: str,
    task_id: str,
    payload: TaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.security_manager})
    task = db.get(Task, task_id)
    _ensure_org_row(task, organization_id, "Task")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.add(task)
    db.commit()
    db.refresh(task)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="task.updated", target_type="task", target_id=task.id)
    return _task_payload(task)


@router.patch("/{organization_id}/tasks/{task_id}/status", tags=["workflow-tasks"])
def update_task_status(
    organization_id: str,
    task_id: str,
    status_value: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    task = db.get(Task, task_id)
    _ensure_org_row(task, organization_id, "Task")
    task.status = status_value
    db.add(task)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="task.status_updated", target_type="task", target_id=task.id, metadata={"status": status_value})
    return {"id": task.id, "status": task.status}


@router.delete("/{organization_id}/tasks/{task_id}", tags=["workflow-tasks"])
def delete_task(
    organization_id: str,
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.security_manager})
    task = db.get(Task, task_id)
    _ensure_org_row(task, organization_id, "Task")
    db.delete(task)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="task.deleted", target_type="task", target_id=task_id)
    return {"deleted": True}


@router.get("/{organization_id}/tasks/export/{export_format}", tags=["workflow-tasks"])
def export_tasks(
    organization_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    rows = db.query(Task).filter(Task.organization_id == organization_id).order_by(Task.created_at.desc()).all()
    payload = [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "assignee_user_id": row.assignee_user_id,
            "due_date": _iso(row.due_date),
            "priority": row.priority,
            "status": row.status,
            "framework_id": row.framework_id,
            "control_id": row.control_id,
        }
        for row in rows
    ]
    return _export_records(organization_id, "tasks", export_format, payload)
