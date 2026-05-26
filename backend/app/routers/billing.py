from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import BillingCustomer, RoleName, Subscription, User
from app.schemas import CheckoutSessionRequest, CheckoutSessionResponse
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

    stripe_configured = bool(settings.stripe_secret_key)
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


def _price_for_plan(plan_name: str) -> str | None:
    plan_map = {
        "starter": settings.stripe_price_starter,
        "growth": settings.stripe_price_growth,
        "enterprise": settings.stripe_price_enterprise,
    }
    return plan_map.get(plan_name.lower())


@router.post("/{organization_id}/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    organization_id: str,
    payload: CheckoutSessionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    if not settings.stripe_secret_key:
        raise HTTPException(status_code=400, detail="Stripe is not configured")

    price_id = _price_for_plan(payload.plan_name)
    if not price_id:
        raise HTTPException(status_code=422, detail="Plan is not available for checkout")

    stripe.api_key = settings.stripe_secret_key
    customer_row = db.query(BillingCustomer).filter(BillingCustomer.organization_id == organization_id).first()
    customer_id = customer_row.provider_customer_id if customer_row else None
    if not customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={"organization_id": organization_id},
            name=user.full_name,
        )
        customer_id = customer["id"]
        customer_row = BillingCustomer(
            organization_id=organization_id,
            provider="stripe",
            provider_customer_id=customer_id,
        )
        db.add(customer_row)
        db.commit()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        metadata={
            "organization_id": organization_id,
            "plan_name": payload.plan_name.lower(),
        },
    )

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="billing.checkout_session_created",
        target_type="billing_session",
        target_id=session["id"],
        metadata={"plan_name": payload.plan_name.lower()},
    )
    return CheckoutSessionResponse(checkout_url=session["url"], session_id=session["id"])


def _upsert_subscription(
    db: Session,
    *,
    organization_id: str,
    provider_subscription_id: str,
    status_value: str,
    plan_name: str,
    period_end: datetime | None,
) -> None:
    sub = db.query(Subscription).filter(Subscription.organization_id == organization_id).first()
    if not sub:
        sub = Subscription(
            organization_id=organization_id,
            plan_name=plan_name,
            status=status_value,
            provider_subscription_id=provider_subscription_id,
            current_period_end=period_end,
        )
    else:
        sub.plan_name = plan_name
        sub.status = status_value
        sub.provider_subscription_id = provider_subscription_id
        sub.current_period_end = period_end
    db.add(sub)
    db.commit()


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.stripe_secret_key or not settings.stripe_webhook_secret:
        raise HTTPException(status_code=400, detail="Stripe webhook is not configured")

    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    if not sig:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        metadata = data_object.get("metadata", {}) or {}
        organization_id = metadata.get("organization_id")
        plan_name = metadata.get("plan_name", "starter")
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")
        if organization_id and customer_id:
            customer_row = db.query(BillingCustomer).filter(BillingCustomer.organization_id == organization_id).first()
            if not customer_row:
                customer_row = BillingCustomer(
                    organization_id=organization_id,
                    provider="stripe",
                    provider_customer_id=customer_id,
                )
                db.add(customer_row)
                db.commit()
            _upsert_subscription(
                db,
                organization_id=organization_id,
                provider_subscription_id=subscription_id,
                status_value="active",
                plan_name=plan_name,
                period_end=None,
            )

    if event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        customer_id = data_object.get("customer")
        provider_subscription_id = data_object.get("id")
        status_value = data_object.get("status", "unknown")
        metadata = data_object.get("metadata", {}) or {}
        plan_name = metadata.get("plan_name")

        customer_row = db.query(BillingCustomer).filter(BillingCustomer.provider_customer_id == customer_id).first()
        if customer_row:
            org_id = customer_row.organization_id
            if not plan_name:
                existing = db.query(Subscription).filter(Subscription.organization_id == org_id).first()
                plan_name = existing.plan_name if existing else "starter"

            period_end_ts = data_object.get("current_period_end")
            period_end = datetime.utcfromtimestamp(period_end_ts) if period_end_ts else None
            _upsert_subscription(
                db,
                organization_id=org_id,
                provider_subscription_id=provider_subscription_id,
                status_value=status_value,
                plan_name=plan_name,
                period_end=period_end,
            )

    return {"received": True}
