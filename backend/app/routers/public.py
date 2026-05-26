from fastapi import APIRouter, HTTPException

from app.legal_templates import LEGAL_DRAFTS

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/legal-pages")
def list_legal_pages():
    return [{"slug": key, "title": value["title"]} for key, value in LEGAL_DRAFTS.items()]


@router.get("/legal-pages/{slug}")
def get_legal_page(slug: str):
    page = LEGAL_DRAFTS.get(slug)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return {**page, "requires_legal_review": True}


@router.get("/health")
def healthcheck():
    return {"status": "ok"}
