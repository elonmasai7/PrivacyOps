from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Membership, Organization, RoleName, User
from app.schemas import (
    InviteMemberRequest,
    MemberProfileResponse,
    MembershipResponse,
    OnboardingAnswersRequest,
    OnboardingResultResponse,
    OrganizationCreateRequest,
    OrganizationResponse,
)
from app.services import calculate_trust_readiness, write_audit_log

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Organization).filter(Organization.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")

    org = Organization(
        name=payload.name.strip(),
        slug=payload.slug,
        country=payload.country,
        industry=payload.industry,
        employee_band=payload.employee_band,
        revenue_band=payload.revenue_band,
    )
    db.add(org)
    db.flush()

    membership = Membership(organization_id=org.id, user_id=user.id, role=RoleName.owner)
    db.add(membership)
    db.commit()
    db.refresh(org)
    write_audit_log(
        db,
        organization_id=org.id,
        actor_user_id=user.id,
        action="organization.created",
        target_type="organization",
        target_id=org.id,
        metadata={"slug": org.slug},
    )
    return org


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    org_ids = [m.organization_id for m in memberships]
    if not org_ids:
        return []
    return db.query(Organization).filter(Organization.id.in_(org_ids)).all()


@router.get("/{organization_id}/membership", response_model=MembershipResponse)
def get_membership(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    return membership


@router.post("/{organization_id}/onboarding", response_model=OnboardingResultResponse)
def submit_onboarding(
    organization_id: str,
    payload: OnboardingAnswersRequest,
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
        },
    )
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    result = calculate_trust_readiness(payload.answers)
    org.trust_readiness_score = result["trust_readiness_score"]
    org.privacy_health_map = {
        "risk_areas": result["risk_areas"],
        "suggested_frameworks": result["suggested_frameworks"],
    }
    org.onboarding_completed = True

    db.add(org)
    db.commit()

    write_audit_log(
        db,
        organization_id=org.id,
        actor_user_id=user.id,
        action="organization.onboarding_completed",
        target_type="organization",
        target_id=org.id,
        metadata={"score": org.trust_readiness_score},
    )
    return OnboardingResultResponse(**result)


@router.post("/{organization_id}/members", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    organization_id: str,
    payload: InviteMemberRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin})

    if membership.role == RoleName.admin and payload.role == RoleName.owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin cannot assign owner role")

    invited = db.query(User).filter(User.email == payload.email.lower()).first()
    if not invited:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist. They must register first before invitation.",
        )

    existing = (
        db.query(Membership)
        .filter(Membership.organization_id == organization_id, Membership.user_id == invited.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already belongs to this organization")

    invited_membership = Membership(organization_id=organization_id, user_id=invited.id, role=payload.role)
    db.add(invited_membership)
    db.commit()
    db.refresh(invited_membership)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="organization.member_invited",
        target_type="membership",
        target_id=invited_membership.id,
        metadata={"invited_email": invited.email, "role": payload.role.value},
    )
    return invited_membership


@router.get("/{organization_id}/members", response_model=list[MemberProfileResponse])
def list_members(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    rows = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.organization_id == organization_id)
        .all()
    )
    return [
        MemberProfileResponse(
            membership_id=membership_obj.id,
            user_id=user_obj.id,
            email=user_obj.email,
            full_name=user_obj.full_name,
            role=membership_obj.role,
        )
        for membership_obj, user_obj in rows
    ]
