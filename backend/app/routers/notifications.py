from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership
from app.models import Notification, User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationCreateRequest(BaseModel):
    user_id: str
    event_type: str
    title: str
    body: str


@router.post("/{organization_id}")
def create_notification(
    organization_id: str,
    payload: NotificationCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    note = Notification(
        organization_id=organization_id,
        user_id=payload.user_id,
        event_type=payload.event_type,
        title=payload.title,
        body=payload.body,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{organization_id}")
def list_notifications(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return (
        db.query(Notification)
        .filter(Notification.organization_id == organization_id, Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.patch("/{organization_id}/{notification_id}/read")
def mark_read(
    organization_id: str,
    notification_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    note = db.get(Notification, notification_id)
    if not note or note.organization_id != organization_id or note.user_id != user.id:
        return {"updated": False}
    note.is_read = True
    db.add(note)
    db.commit()
    return {"updated": True}
