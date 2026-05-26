from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import ProcessingActivity, RoleName, User
from app.schemas import ProcessingActivityCreateRequest, ProcessingActivityResponse
from app.services import write_audit_log

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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return (
        db.query(ProcessingActivity)
        .filter(ProcessingActivity.organization_id == organization_id)
        .order_by(ProcessingActivity.created_at.desc())
        .all()
    )
