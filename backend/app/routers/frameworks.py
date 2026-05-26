from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Framework, FrameworkStatus, FrameworkVersion, Membership, RoleName, User
from app.schemas import FrameworkCreateRequest, FrameworkResponse
from app.services import write_audit_log

router = APIRouter(prefix="/frameworks", tags=["frameworks"])


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
        reviewer_name=user.full_name,
        last_reviewed_at=datetime.utcnow(),
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
