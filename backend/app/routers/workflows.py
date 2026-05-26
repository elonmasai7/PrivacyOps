from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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
from app.services import write_audit_log

router = APIRouter(prefix="/workflows", tags=["workflows"])


class VendorCreate(BaseModel):
    name: str
    service_provided: str
    data_processed: str
    country: str
    contract_status: str
    dpa_status: str
    security_review_status: str
    risk_level: str
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


class DSRCreate(BaseModel):
    request_type: str
    requester_email: str
    due_date: datetime | None = None
    internal_notes: str | None = None


class PolicyCreate(BaseModel):
    name: str
    body_markdown: str


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    priority: str = "medium"


@router.post("/{organization_id}/vendors", status_code=status.HTTP_201_CREATED)
def create_vendor(
    organization_id: str,
    payload: VendorCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    vendor = Vendor(organization_id=organization_id, owner_user_id=user.id, subprocessors=[], **payload.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="vendor.created", target_type="vendor", target_id=vendor.id)
    return vendor


@router.get("/{organization_id}/vendors")
def list_vendors(organization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_org_membership(organization_id, user, db)
    return db.query(Vendor).filter(Vendor.organization_id == organization_id).all()


@router.post("/{organization_id}/incidents", status_code=status.HTTP_201_CREATED)
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
    return incident


@router.get("/{organization_id}/incidents")
def list_incidents(organization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_org_membership(organization_id, user, db)
    return db.query(Incident).filter(Incident.organization_id == organization_id).all()


@router.post("/{organization_id}/dsr", status_code=status.HTTP_201_CREATED)
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
    return dsr


@router.get("/{organization_id}/dsr")
def list_dsr(organization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_org_membership(organization_id, user, db)
    return db.query(DataSubjectRequest).filter(DataSubjectRequest.organization_id == organization_id).all()


@router.post("/{organization_id}/policies", status_code=status.HTTP_201_CREATED)
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
    return {
        "id": policy.id,
        "name": policy.name,
        "status": policy.status,
        "requires_legal_review": True,
    }


@router.get("/{organization_id}/policies")
def list_policies(organization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_org_membership(organization_id, user, db)
    return db.query(Policy).filter(Policy.organization_id == organization_id).all()


@router.post("/{organization_id}/tasks", status_code=status.HTTP_201_CREATED)
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
    return task


@router.patch("/{organization_id}/tasks/{task_id}/status")
def update_task_status(
    organization_id: str,
    task_id: str,
    status_value: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    task = db.get(Task, task_id)
    if not task or task.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task.status = status_value
    db.add(task)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="task.status_updated", target_type="task", target_id=task.id, metadata={"status": status_value})
    return {"id": task.id, "status": task.status}


@router.get("/{organization_id}/tasks")
def list_tasks(organization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_org_membership(organization_id, user, db)
    return db.query(Task).filter(Task.organization_id == organization_id).all()
