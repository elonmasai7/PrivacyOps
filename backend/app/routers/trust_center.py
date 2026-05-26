from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_org_membership, require_role
from app.models import RoleName, TrustCenterDocument, TrustCenterPage, User
from app.services import write_audit_log

router = APIRouter(prefix="/trust-center", tags=["trust_center"])


class TrustPageCreate(BaseModel):
    slug: str
    title: str
    is_public: bool = False
    content_markdown: str


@router.post("/{organization_id}/pages", status_code=status.HTTP_201_CREATED)
def create_trust_page(
    organization_id: str,
    payload: TrustPageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})

    page = TrustCenterPage(organization_id=organization_id, **payload.model_dump())
    db.add(page)
    db.commit()
    db.refresh(page)
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="trust_center.page_created", target_type="trust_center_page", target_id=page.id)
    return page


@router.get("/{organization_id}/pages")
def list_trust_pages(organization_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_org_membership(organization_id, user, db)
    return db.query(TrustCenterPage).filter(TrustCenterPage.organization_id == organization_id).all()


@router.post("/{organization_id}/documents/{document_id}/approve")
def approve_document(
    organization_id: str,
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_org_membership(organization_id, user, db)
    require_role(membership, {RoleName.owner, RoleName.admin, RoleName.compliance_manager})
    doc = db.get(TrustCenterDocument, document_id)
    if not doc or doc.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    doc.is_approved = True
    db.add(doc)
    db.commit()
    write_audit_log(db, organization_id=organization_id, actor_user_id=user.id, action="trust_center.document_approved", target_type="trust_center_document", target_id=doc.id)
    return {"id": doc.id, "is_approved": doc.is_approved}


@router.get("/public/{organization_id}")
def public_trust_center(organization_id: str, db: Session = Depends(get_db)):
    pages = db.query(TrustCenterPage).filter(TrustCenterPage.organization_id == organization_id, TrustCenterPage.is_public.is_(True)).all()
    docs = (
        db.query(TrustCenterDocument)
        .filter(
            TrustCenterDocument.organization_id == organization_id,
            TrustCenterDocument.is_approved.is_(True),
            TrustCenterDocument.visibility == "public",
        )
        .all()
    )
    return {
        "pages": [{"slug": page.slug, "title": page.title, "content_markdown": page.content_markdown} for page in pages],
        "documents": [{"id": doc.id, "title": doc.title} for doc in docs],
    }
