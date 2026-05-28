import csv
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import ProcessingActivity, RoleName, User
from app.schemas import ProcessingActivityCreateRequest, ProcessingActivityResponse
from app.services import ensure_dir, write_audit_log

router = APIRouter(prefix="/processing-activities", tags=["processing_activities"])


@router.post("/{organization_id}", response_model=ProcessingActivityResponse, status_code=status.HTTP_201_CREATED)
def create_processing_activity(
    organization_id: str,
    payload: ProcessingActivityCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(
        membership,
        {
            RoleName.owner,
            RoleName.admin,
            RoleName.compliance_manager,
            RoleName.member,
        },
    )

    activity = ProcessingActivity(
        organization_id=organization_id,
        name=payload.name,
        data_categories=payload.data_categories,
        data_subject_categories=payload.data_subject_categories,
        purpose=payload.purpose,
        lawful_basis=payload.lawful_basis,
        system_name=payload.system_name,
        data_location=payload.data_location,
        vendor_name=payload.vendor_name,
        retention_period=payload.retention_period,
        security_measures=payload.security_measures,
        cross_border_transfer=payload.cross_border_transfer,
        owner_user_id=user.id,
        risk_level=payload.risk_level,
        review_date=payload.review_date,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="processing_activity.created",
        target_type="processing_activity",
        target_id=activity.id,
    )
    return activity


@router.get("/{organization_id}", response_model=list[ProcessingActivityResponse])
def list_processing_activities(
    organization_id: str,
    query: str | None = Query(default=None),
    lawful_basis: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    activities = db.query(ProcessingActivity).filter(ProcessingActivity.organization_id == organization_id)
    if query:
        activities = activities.filter(ProcessingActivity.name.ilike(f"%{query}%"))
    if lawful_basis:
        activities = activities.filter(ProcessingActivity.lawful_basis == lawful_basis)
    if risk_level:
        activities = activities.filter(ProcessingActivity.risk_level == risk_level)
    return activities.order_by(ProcessingActivity.created_at.desc()).offset(offset).limit(limit).all()


@router.patch("/{organization_id}/{activity_id}", response_model=ProcessingActivityResponse)
def update_processing_activity(
    organization_id: str,
    activity_id: str,
    payload: ProcessingActivityCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(
        membership,
        {
            RoleName.owner,
            RoleName.admin,
            RoleName.compliance_manager,
            RoleName.member,
        },
    )

    activity = db.get(ProcessingActivity, activity_id)
    if not activity or activity.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing activity not found")

    update = payload.model_dump()
    for key, value in update.items():
        setattr(activity, key, value)
    activity.owner_user_id = user.id
    db.add(activity)
    db.commit()
    db.refresh(activity)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="processing_activity.updated",
        target_type="processing_activity",
        target_id=activity.id,
    )
    return activity


@router.delete("/{organization_id}/{activity_id}")
def delete_processing_activity(
    organization_id: str,
    activity_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})

    activity = db.get(ProcessingActivity, activity_id)
    if not activity or activity.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing activity not found")
    db.delete(activity)
    db.commit()

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="processing_activity.deleted",
        target_type="processing_activity",
        target_id=activity_id,
    )
    return {"deleted": True}


@router.get("/{organization_id}/export/{export_format}")
def export_processing_activities(
    organization_id: str,
    export_format: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    export_format = export_format.lower()
    if export_format not in {"json", "csv", "pdf"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported export format")

    activities = (
        db.query(ProcessingActivity)
        .filter(ProcessingActivity.organization_id == organization_id)
        .order_by(ProcessingActivity.created_at.desc())
        .all()
    )
    export_dir = ensure_dir(f"exports/{organization_id}/processing-activities")
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    if export_format == "json":
        file_path = Path(export_dir) / f"processing-activities-{stamp}.json"
        payload = [
            {
                "id": item.id,
                "name": item.name,
                "purpose": item.purpose,
                "lawful_basis": item.lawful_basis,
                "data_categories": item.data_categories,
                "data_subject_categories": item.data_subject_categories,
                "system_name": item.system_name,
                "data_location": item.data_location,
                "vendor_name": item.vendor_name,
                "retention_period": item.retention_period,
                "security_measures": item.security_measures,
                "cross_border_transfer": item.cross_border_transfer,
                "risk_level": item.risk_level,
                "review_date": item.review_date.isoformat() if item.review_date else None,
            }
            for item in activities
        ]
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return FileResponse(str(file_path), media_type="application/json", filename=file_path.name)

    if export_format == "csv":
        file_path = Path(export_dir) / f"processing-activities-{stamp}.csv"
        with file_path.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    "id",
                    "name",
                    "purpose",
                    "lawful_basis",
                    "data_categories",
                    "data_subject_categories",
                    "system_name",
                    "data_location",
                    "vendor_name",
                    "retention_period",
                    "security_measures",
                    "cross_border_transfer",
                    "risk_level",
                    "review_date",
                ]
            )
            for item in activities:
                writer.writerow(
                    [
                        item.id,
                        item.name,
                        item.purpose,
                        item.lawful_basis,
                        json.dumps(item.data_categories),
                        json.dumps(item.data_subject_categories),
                        item.system_name,
                        item.data_location,
                        item.vendor_name,
                        item.retention_period,
                        item.security_measures,
                        item.cross_border_transfer,
                        item.risk_level,
                        item.review_date.isoformat() if item.review_date else "",
                    ]
                )
        return FileResponse(str(file_path), media_type="text/csv", filename=file_path.name)

    file_path = Path(export_dir) / f"processing-activities-{stamp}.pdf"
    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    y = 800
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "PrivacyOps Africa Core - Data Inventory Export")
    y -= 24
    pdf.setFont("Helvetica", 9)
    for item in activities:
        line = f"{item.name} | Basis: {item.lawful_basis} | Risk: {item.risk_level} | System: {item.system_name}"
        pdf.drawString(40, y, line[:120])
        y -= 14
        if y < 80:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            y = 800
    pdf.save()
    return FileResponse(str(file_path), media_type="application/pdf", filename=file_path.name)
