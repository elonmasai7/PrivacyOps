import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import BillingCustomer, RoleName, Subscription, User
from app.services import write_audit_log

router = APIRouter(prefix="/billing", tags=["billing"])


class SubscriptionUpdateRequest(BaseModel):
    plan_name: str
    status: str


@router.get("/{organization_id}")
def get_billing_status(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    sub = db.query(Subscription).filter(Subscription.organization_id == organization_id).first()
    customer = db.query(BillingCustomer).filter(BillingCustomer.organization_id == organization_id).first()

    stripe_configured = bool(os.getenv("STRIPE_SECRET_KEY"))
    if not stripe_configured:
        return {
            "status": "not_configured",
            "message": "Stripe key is missing. Configure STRIPE_SECRET_KEY to enable live billing.",
            "subscription": None,
            "customer": None,
        }

    return {
        "status": "configured",
        "subscription": {
            "plan_name": sub.plan_name if sub else None,
            "state": sub.status if sub else "none",
            "current_period_end": sub.current_period_end if sub else None,
        },
        "customer": {
            "provider": customer.provider,
            "provider_customer_id": customer.provider_customer_id,
        }
        if customer
        else None,
    }


@router.post("/{organization_id}/admin-override", status_code=status.HTTP_201_CREATED)
def admin_override_subscription(
    organization_id: str,
    payload: SubscriptionUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner})

    subscription = db.query(Subscription).filter(Subscription.organization_id == organization_id).first()
    if not subscription:
        subscription = Subscription(organization_id=organization_id, plan_name=payload.plan_name, status=payload.status)
    else:
        subscription.plan_name = payload.plan_name
        subscription.status = payload.status
    subscription.current_period_end = datetime.utcnow()
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="billing.admin_override",
        target_type="subscription",
        target_id=subscription.id,
    )
    return subscription
