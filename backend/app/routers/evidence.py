import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import Evidence, EvidenceVersion, RoleName, User
from app.schemas import EvidenceResponse
from app.services import ensure_dir, hash_file, write_audit_log

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/{organization_id}/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    organization_id: str,
    title: str = Form(...),
    source: str = Form(...),
    collection_method: str = Form(...),
    description: str | None = Form(default=None),
    framework_id: str | None = Form(default=None),
    control_id: str | None = Form(default=None),
    expiry_date: str | None = Form(default=None),
    file: UploadFile = File(...),
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
            RoleName.security_manager,
            RoleName.member,
        },
    )

    file_bytes = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds max size")

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Filename is required")

    org_dir = ensure_dir(os.path.join(settings.upload_dir, organization_id))
    filename = f"{uuid.uuid4()}-{file.filename}"
    path = org_dir / filename
    path.write_bytes(file_bytes)

    file_digest = hash_file(file_bytes)
    parsed_expiry = datetime.fromisoformat(expiry_date) if expiry_date else None

    evidence = Evidence(
        organization_id=organization_id,
        framework_id=framework_id,
        control_id=control_id,
        owner_user_id=user.id,
        source=source,
        collection_method=collection_method,
        title=title,
        description=description,
        file_path=str(path),
        file_hash=file_digest,
        expiry_date=parsed_expiry,
    )
    db.add(evidence)
    db.flush()

    version = EvidenceVersion(
        evidence_id=evidence.id,
        version_number=1,
        file_path=str(path),
        file_hash=file_digest,
        created_by_user_id=user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(evidence)

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=user.id,
        action="evidence.uploaded",
        target_type="evidence",
        target_id=evidence.id,
        metadata={"file": file.filename},
    )
    return evidence


@router.get("/{organization_id}", response_model=list[EvidenceResponse])
def list_evidence(
    organization_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_membership(organization_id, user, db)
    return db.query(Evidence).filter(Evidence.organization_id == organization_id).all()
