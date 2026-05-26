import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import httpx
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AuditLog, Integration, SecurityFinding


def write_audit_log(
    db: Session,
    *,
    organization_id: str | None,
    actor_user_id: str | None,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
) -> None:
    log = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        event_metadata=metadata or {},
    )
    db.add(log)
    db.commit()


def calculate_trust_readiness(answers: dict) -> dict:
    weights = {
        "handles_personal_data": 10,
        "handles_sensitive_data": 12,
        "serves_eu_users": 10,
        "has_privacy_policy": 8,
        "has_dpo": 8,
        "has_security_policies": 10,
        "has_incident_response": 10,
        "uses_cloud_services": 7,
        "uses_third_party_vendors": 7,
        "soc2_or_iso_required": 8,
        "processes_childrens_data": 10,
    }

    positive_score = 0
    risk_areas: list[str] = []
    for key, weight in weights.items():
        value = bool(answers.get(key, False))
        if key in {
            "has_privacy_policy",
            "has_dpo",
            "has_security_policies",
            "has_incident_response",
        }:
            if value:
                positive_score += weight
            else:
                risk_areas.append(key)
        else:
            if value:
                positive_score += int(weight * 0.5)
                if key in {"handles_sensitive_data", "processes_childrens_data"}:
                    risk_areas.append(key)
            else:
                positive_score += weight

    suggested_frameworks = ["Kenya Data Protection Act", "GDPR"]
    if answers.get("soc2_or_iso_required"):
        suggested_frameworks.extend(["SOC 2 Readiness", "ISO 27001 Readiness"])

    required_workflows = [
        "Data inventory",
        "RoPA",
        "Evidence vault",
        "Incident and breach workflow",
        "Vendor risk review",
    ]
    missing_evidence = [
        "Privacy policy" if not answers.get("has_privacy_policy") else "",
        "Security policy" if not answers.get("has_security_policies") else "",
        "Incident response procedure" if not answers.get("has_incident_response") else "",
    ]

    score = max(0, min(100, positive_score))
    return {
        "trust_readiness_score": score,
        "suggested_frameworks": suggested_frameworks,
        "required_workflows": required_workflows,
        "risk_areas": risk_areas,
        "recommended_next_actions": [
            "Complete onboarding evidence checklist",
            "Assign control owners",
            "Connect at least one integration for automation",
        ],
        "missing_evidence": [item for item in missing_evidence if item],
    }


def hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_report_files(base_dir: str, report_id: str, payload: dict) -> dict[str, str]:
    export_dir = ensure_dir(base_dir)

    json_path = export_dir / f"{report_id}.json"
    csv_path = export_dir / f"{report_id}.csv"
    docx_path = export_dir / f"{report_id}.docx"
    pdf_path = export_dir / f"{report_id}.pdf"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["key", "value"])
        for key, value in payload.items():
            writer.writerow([key, json.dumps(value)])

    doc = Document()
    doc.add_heading("PrivacyOps Africa Report", level=1)
    for key, value in payload.items():
        doc.add_paragraph(f"{key}: {json.dumps(value)}")
    doc.save(docx_path)

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    y = 800
    c.setFont("Helvetica", 12)
    c.drawString(40, y, "PrivacyOps Africa Report")
    y -= 30
    for key, value in payload.items():
        text = f"{key}: {json.dumps(value)}"
        c.drawString(40, y, text[:110])
        y -= 18
        if y < 80:
            c.showPage()
            y = 800
    c.save()

    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "docx": str(docx_path),
        "pdf": str(pdf_path),
    }


def ai_guardrailed_response(prompt: str, context: dict) -> dict:
    legal_keywords = ["lawful basis", "contract", "regulator", "legal", "breach"]
    requires_legal_review = any(keyword in prompt.lower() for keyword in legal_keywords)

    guidance = (
        "This guidance is generated for compliance operations and does not replace legal advice. "
        "Use the listed controls, collected evidence, and your internal counsel for final decisions."
    )
    if context.get("gap_summary"):
        guidance += f" Gap focus: {context['gap_summary']}."

    return {
        "guidance": guidance,
        "confidence_level": "medium",
        "requires_legal_review": requires_legal_review,
        "source_references": context.get("source_references", []),
        "next_action": "Assign a compliance owner, attach evidence, and route legal-sensitive items for counsel review.",
    }


async def scan_github(integration: Integration, db: Session) -> list[SecurityFinding]:
    token = integration.config.get("personal_access_token")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    findings: list[SecurityFinding] = []
    async with httpx.AsyncClient(timeout=30) as client:
        repos_response = await client.get(f"{settings.github_api_base}/user/repos", headers=headers)
        repos_response.raise_for_status()
        repos = repos_response.json()

        for repo in repos[:50]:
            if repo.get("private") is False:
                findings.append(
                    SecurityFinding(
                        organization_id=integration.organization_id,
                        integration_id=integration.id,
                        title=f"Public repository detected: {repo['full_name']}",
                        severity="medium",
                        category="repository_visibility",
                        details={"repo": repo["full_name"], "visibility": "public"},
                    )
                )

            repo_name = repo["name"]
            owner = repo["owner"]["login"]
            branch_resp = await client.get(
                f"{settings.github_api_base}/repos/{owner}/{repo_name}/branches/{repo['default_branch']}",
                headers=headers,
            )
            if branch_resp.status_code == 200:
                protection = branch_resp.json().get("protected", False)
                if not protection:
                    findings.append(
                        SecurityFinding(
                            organization_id=integration.organization_id,
                            integration_id=integration.id,
                            title=f"Branch protection missing: {repo['full_name']}",
                            severity="high",
                            category="branch_protection",
                            details={"repo": repo["full_name"], "default_branch": repo["default_branch"]},
                        )
                    )

    for finding in findings:
        db.add(finding)
    integration.last_synced_at = datetime.utcnow()
    integration.status = "connected"
    integration.last_error = None
    db.add(integration)
    db.commit()
    return findings
