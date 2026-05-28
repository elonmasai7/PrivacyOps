from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Control, Framework, FrameworkStatus, FrameworkVersion, Membership, RoleName, User
from app.schemas import FrameworkCreateRequest, FrameworkResponse
from app.services import write_audit_log

router = APIRouter(prefix="/frameworks", tags=["frameworks"])

VALID_REVIEW_STATUS = {"community-reviewed", "expert-reviewed", "unverified"}


class FrameworkPackControl(BaseModel):
    category: str
    title: str
    requirement_text: str
    evidence_expectation: str | None = None
    risk_weight: int = Field(default=1, ge=1, le=10)
    mappings: dict = Field(default_factory=dict)


class FrameworkPackImportRequest(BaseModel):
    name: str
    jurisdiction: str
    source_reference: str | None = None
    status: str = "draft"
    version: str = "1.0.0"
    review_status: str = "unverified"
    reviewer_notes: str | None = None
    controls: list[FrameworkPackControl] = Field(default_factory=list)


class FrameworkPackReviewUpdateRequest(BaseModel):
    review_status: str
    reviewer_notes: str | None = None


@router.get("", response_model=list[FrameworkResponse])
def list_frameworks(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Framework).order_by(Framework.name.asc()).all()


@router.post("/{organization_id}", response_model=FrameworkResponse, status_code=status.HTTP_201_CREATED)
def create_framework(
    organization_id: str,
    payload: FrameworkCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership: Membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    try:
        status_value = FrameworkStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid framework status") from exc

    framework = Framework(
        name=payload.name,
        jurisdiction=payload.jurisdiction,
        source_reference=payload.source_reference,
        status=status_value,
    )
    db.add(framework)
    db.flush()

    version = FrameworkVersion(
        framework_id=framework.id,
        version="1.0.0",
        review_status="unverified",
        reviewer_name=user.full_name,
        last_reviewed_at=datetime.utcnow(),
        source_reference=payload.source_reference,
        changelog={"initial": "Created by organization admin"},
    )
    db.add(version)
    db.commit()
    db.refresh(framework)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="framework.created",
        target_type="framework",
        target_id=framework.id,
    )
    return framework


@router.post("/{organization_id}/packs/import", status_code=status.HTTP_201_CREATED)
def import_framework_pack(
    organization_id: str,
    payload: FrameworkPackImportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership: Membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    if payload.review_status not in VALID_REVIEW_STATUS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid review status")

    try:
        status_value = FrameworkStatus(payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid framework status") from exc

    framework = Framework(
        name=payload.name,
        jurisdiction=payload.jurisdiction,
        source_reference=payload.source_reference,
        status=status_value,
    )
    db.add(framework)
    db.flush()

    version = FrameworkVersion(
        framework_id=framework.id,
        version=payload.version,
        review_status=payload.review_status,
        reviewer_name=user.full_name,
        last_reviewed_at=datetime.utcnow(),
        reviewer_notes=payload.reviewer_notes,
        source_reference=payload.source_reference,
        changelog={
            "type": "framework_pack_import",
            "controls": len(payload.controls),
            "imported_by": user.email,
            "imported_at": datetime.utcnow().isoformat(),
        },
    )
    db.add(version)
    db.flush()

    for control in payload.controls:
        db.add(
            Control(
                framework_version_id=version.id,
                category=control.category,
                title=control.title,
                requirement_text=control.requirement_text,
                evidence_expectation=control.evidence_expectation,
                risk_weight=control.risk_weight,
                mappings=control.mappings,
            )
        )

    db.commit()

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="framework.pack_imported",
        target_type="framework",
        target_id=framework.id,
        metadata={"version": payload.version, "controls": len(payload.controls), "review_status": payload.review_status},
    )

    return {
        "framework_id": framework.id,
        "framework_name": framework.name,
        "version": payload.version,
        "review_status": payload.review_status,
        "controls_imported": len(payload.controls),
    }


@router.get("/{organization_id}/{framework_id}/packs/export")
def export_framework_pack(
    organization_id: str,
    framework_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    framework = db.get(Framework, framework_id)
    if not framework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found")

    version = (
        db.query(FrameworkVersion)
        .filter(FrameworkVersion.framework_id == framework.id)
        .order_by(FrameworkVersion.created_at.desc())
        .first()
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework version not found")

    controls = (
        db.query(Control)
        .filter(Control.framework_version_id == version.id)
        .order_by(Control.category.asc(), Control.title.asc())
        .all()
    )

    return {
        "framework": {
            "id": framework.id,
            "name": framework.name,
            "jurisdiction": framework.jurisdiction,
            "source_reference": framework.source_reference,
            "status": framework.status.value,
        },
        "version": {
            "id": version.id,
            "version": version.version,
            "review_status": version.review_status,
            "reviewer_name": version.reviewer_name,
            "reviewer_notes": version.reviewer_notes,
            "last_reviewed_at": version.last_reviewed_at,
            "changelog": version.changelog,
        },
        "controls": [
            {
                "id": control.id,
                "category": control.category,
                "title": control.title,
                "requirement_text": control.requirement_text,
                "evidence_expectation": control.evidence_expectation,
                "risk_weight": control.risk_weight,
                "mappings": control.mappings,
            }
            for control in controls
        ],
    }


@router.patch("/{organization_id}/versions/{version_id}/review")
def update_framework_pack_review(
    organization_id: str,
    version_id: str,
    payload: FrameworkPackReviewUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership: Membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager, RoleName.auditor})

    if payload.review_status not in VALID_REVIEW_STATUS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid review status")

    version = db.get(FrameworkVersion, version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework version not found")

    version.review_status = payload.review_status
    version.reviewer_notes = payload.reviewer_notes
    version.reviewer_name = user.full_name
    version.last_reviewed_at = datetime.utcnow()
    db.add(version)
    db.commit()

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="framework.pack_review_updated",
        target_type="framework_version",
        target_id=version.id,
        metadata={"review_status": payload.review_status},
    )
    return {
        "version_id": version.id,
        "review_status": version.review_status,
        "reviewer_name": version.reviewer_name,
        "last_reviewed_at": version.last_reviewed_at,
    }
