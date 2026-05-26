from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import AuditLog, RoleName, User

router = APIRouter(prefix="/audit-logs", tags=["audit_logs"])


@router.get("/{organization_id}")
def list_audit_logs(
    organization_id: str,
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
            RoleName.auditor,
            RoleName.viewer,
        },
    )
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": item.id,
            "action": item.action,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "metadata": item.event_metadata,
            "created_at": item.created_at,
        }
        for item in logs
    ]
