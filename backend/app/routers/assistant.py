from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership
from app.models import SystemSetting, User
from app.schemas import AIRequest, AIResponse
from app.services import ai_guardrailed_response, write_audit_log

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/{organization_id}", response_model=AIResponse)
def ask_assistant(
    organization_id: str,
    payload: AIRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    ai_setting = (
        db.query(SystemSetting)
        .filter(SystemSetting.organization_id == organization_id, SystemSetting.key == "ai_assistant_enabled")
        .first()
    )
    enabled = ai_setting.value.lower() == "true" if ai_setting else False
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI assistant is disabled. Enable system setting ai_assistant_enabled=true to use this module.",
        )
    response = ai_guardrailed_response(payload.prompt, payload.context)
    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="assistant.requested",
        target_type="assistant",
        target_id=organization_id,
        metadata={"requires_legal_review": response["requires_legal_review"]},
    )
    return response
