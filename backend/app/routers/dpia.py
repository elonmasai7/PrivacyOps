from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Dpia, DpiaAnswer, RoleName, User
from app.services import write_audit_log

router = APIRouter(prefix="/dpia", tags=["dpia"])


class DpiaCreateRequest(BaseModel):
    title: str
    answers: dict[str, str]
    mitigation_plan: str | None = None


@router.post("/{organization_id}", status_code=status.HTTP_201_CREATED)
def create_dpia(
    organization_id: str,
    payload: DpiaCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})

    risky_answers = [k for k, v in payload.answers.items() if v.lower() in {"yes", "high", "large-scale"}]
    risk_score = min(100, len(risky_answers) * 12)
    screening_result = "dpia_required" if risk_score >= 30 else "light_assessment"

    dpia = Dpia(
        organization_id=organization_id,
        title=payload.title,
        screening_result=screening_result,
        risk_score=risk_score,
        mitigation_plan=payload.mitigation_plan,
    )
    db.add(dpia)
    db.flush()

    for question_key, answer_value in payload.answers.items():
        db.add(DpiaAnswer(dpia_id=dpia.id, question_key=question_key, answer_value=answer_value))

    db.commit()
    db.refresh(dpia)
    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="dpia.created",
        target_type="dpia",
        target_id=dpia.id,
        metadata={"risk_score": risk_score},
    )
    return {
        "id": dpia.id,
        "title": dpia.title,
        "risk_score": dpia.risk_score,
        "screening_result": dpia.screening_result,
        "approval_status": dpia.approval_status,
    }


@router.get("/{organization_id}")
def list_dpias(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return db.query(Dpia).filter(Dpia.organization_id == organization_id).all()
