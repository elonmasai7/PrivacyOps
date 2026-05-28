from io import BytesIO


def register_and_login(client, email: str, full_name: str = "User", password: str = "StrongPassword123"):
    register = client.post(
        "/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert register.status_code == 201, register.text
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def create_org(client, token: str, slug: str = "acme-kenya"):
    response = client.post(
        "/organizations",
        headers=auth_headers(token),
        json={
            "name": "Acme Kenya",
            "slug": slug,
            "country": "Kenya",
            "industry": "fintech",
            "employee_band": "11-50",
            "revenue_band": "100k-500k",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_end_to_end_core_acceptance(client):
    token = register_and_login(client, "owner@example.com", "Owner")
    org_id = create_org(client, token)

    onboarding = client.post(
        f"/organizations/{org_id}/onboarding",
        headers=auth_headers(token),
        json={
            "answers": {
                "handles_personal_data": True,
                "handles_sensitive_data": True,
                "serves_eu_users": True,
                "processes_childrens_data": False,
                "uses_cloud_services": True,
                "uses_third_party_vendors": True,
                "has_privacy_policy": True,
                "has_dpo": True,
                "has_security_policies": True,
                "has_incident_response": True,
                "soc2_or_iso_required": True,
            }
        },
    )
    assert onboarding.status_code == 200, onboarding.text
    assert onboarding.json()["trust_readiness_score"] >= 1

    activity = client.post(
        f"/processing-activities/{org_id}",
        headers=auth_headers(token),
        json={
            "name": "Customer onboarding KYC",
            "data_categories": ["national_id", "phone_number"],
            "data_subject_categories": ["customers"],
            "purpose": "Perform customer due diligence",
            "lawful_basis": "legal_obligation",
            "system_name": "KYC Core",
            "data_location": "Nairobi region",
            "vendor_name": "",
            "retention_period": "7 years",
            "security_measures": "Encryption and RBAC",
            "cross_border_transfer": False,
            "risk_level": "medium",
        },
    )
    assert activity.status_code == 201, activity.text

    evidence = client.post(
        f"/evidence/{org_id}/upload",
        headers=auth_headers(token),
        files={"file": ("policy.txt", BytesIO(b"policy content"), "text/plain")},
        data={
            "title": "Security Policy",
            "source": "uploaded_document",
            "collection_method": "manual",
        },
    )
    assert evidence.status_code == 201, evidence.text

    report = client.post(
        f"/reports/{org_id}",
        headers=auth_headers(token),
        json={"report_type": "board_summary", "framework": "Kenya Data Protection Act"},
    )
    assert report.status_code == 201, report.text
    report_id = report.json()["id"]

    export = client.get(
        f"/reports/{org_id}/{report_id}/export/json",
        headers=auth_headers(token),
    )
    assert export.status_code == 200, export.text


def test_org_isolation_and_rbac(client):
    owner_token = register_and_login(client, "owner2@example.com", "Owner Two")
    member_token = register_and_login(client, "member@example.com", "Member")
    outsider_token = register_and_login(client, "outsider@example.com", "Outsider")

    org_id = create_org(client, owner_token, slug="secure-africa")

    invite = client.post(
        f"/organizations/{org_id}/members",
        headers=auth_headers(owner_token),
        json={"email": "member@example.com", "role": "member"},
    )
    assert invite.status_code == 201, invite.text

    forbidden_framework = client.post(
        f"/frameworks/{org_id}",
        headers=auth_headers(member_token),
        json={
            "name": "Kenya DPA Readiness",
            "jurisdiction": "Kenya",
            "source_reference": "https://www.odpc.go.ke/",
            "status": "draft",
        },
    )
    assert forbidden_framework.status_code == 403, forbidden_framework.text

    outsider_access = client.get(
        f"/processing-activities/{org_id}",
        headers=auth_headers(outsider_token),
    )
    assert outsider_access.status_code == 403, outsider_access.text


def test_processing_activity_update_delete_and_export(client):
    token = register_and_login(client, "inventory-owner@example.com", "Inventory Owner")
    org_id = create_org(client, token, slug="inventory-africa")

    create = client.post(
        f"/processing-activities/{org_id}",
        headers=auth_headers(token),
        json={
            "name": "Student admissions data processing",
            "data_categories": ["email", "national_id"],
            "data_subject_categories": ["students"],
            "purpose": "Admissions and enrollment",
            "lawful_basis": "contract",
            "system_name": "Admissions Core",
            "data_location": "Kenya",
            "vendor_name": "",
            "retention_period": "5 years",
            "security_measures": "Encryption and least privilege",
            "cross_border_transfer": False,
            "risk_level": "medium",
        },
    )
    assert create.status_code == 201, create.text
    activity_id = create.json()["id"]

    update = client.patch(
        f"/processing-activities/{org_id}/{activity_id}",
        headers=auth_headers(token),
        json={
            "name": "Student admissions data processing",
            "data_categories": ["email", "national_id"],
            "data_subject_categories": ["students"],
            "purpose": "Admissions and enrollment",
            "lawful_basis": "legal_obligation",
            "system_name": "Admissions Core",
            "data_location": "Kenya",
            "vendor_name": "",
            "retention_period": "5 years",
            "security_measures": "Encryption and least privilege",
            "cross_border_transfer": False,
            "risk_level": "high",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["risk_level"] == "high"

    export_csv = client.get(f"/processing-activities/{org_id}/export/csv", headers=auth_headers(token))
    assert export_csv.status_code == 200, export_csv.text

    delete = client.delete(f"/processing-activities/{org_id}/{activity_id}", headers=auth_headers(token))
    assert delete.status_code == 200, delete.text
    assert delete.json()["deleted"] is True


def test_workflow_crud_filter_export_parity(client):
    token = register_and_login(client, "workflow-owner@example.com", "Workflow Owner")
    org_id = create_org(client, token, slug="workflow-africa")

    vendor = client.post(
        f"/workflows/{org_id}/vendors",
        headers=auth_headers(token),
        json={
            "name": "Cloud Processor",
            "service_provided": "Cloud hosting",
            "data_processed": "Customer profiles",
            "country": "Kenya",
            "subprocessors": ["Backup Operator"],
            "contract_status": "active",
            "dpa_status": "signed",
            "security_review_status": "passed",
            "risk_level": "medium",
        },
    )
    assert vendor.status_code == 201, vendor.text
    vendor_list_initial = client.get(f"/workflows/{org_id}/vendors", headers=auth_headers(token))
    vendor_id = vendor_list_initial.json()[0]["id"]

    vendor_update = client.patch(
        f"/workflows/{org_id}/vendors/{vendor_id}",
        headers=auth_headers(token),
        json={"risk_level": "high", "notes": "Annual review pending"},
    )
    assert vendor_update.status_code == 200, vendor_update.text
    assert vendor_update.json()["risk_level"] == "high"

    vendor_list = client.get(f"/workflows/{org_id}/vendors?risk_level=high", headers=auth_headers(token))
    assert vendor_list.status_code == 200, vendor_list.text
    assert len(vendor_list.json()) == 1

    vendor_export = client.get(f"/workflows/{org_id}/vendors/export/csv", headers=auth_headers(token))
    assert vendor_export.status_code == 200, vendor_export.text

    incident = client.post(
        f"/workflows/{org_id}/incidents",
        headers=auth_headers(token),
        json={
            "title": "Unauthorized access attempt",
            "severity": "high",
            "affected_systems": ["api"],
            "affected_data_categories": ["email"],
            "affected_data_subjects": 2,
        },
    )
    assert incident.status_code == 201, incident.text
    incident_id = client.get(f"/workflows/{org_id}/incidents", headers=auth_headers(token)).json()[0]["id"]

    incident_update = client.patch(
        f"/workflows/{org_id}/incidents/{incident_id}",
        headers=auth_headers(token),
        json={"status": "closed", "root_cause": "credential stuffing"},
    )
    assert incident_update.status_code == 200, incident_update.text
    assert incident_update.json()["status"] == "closed"

    incident_export = client.get(f"/workflows/{org_id}/incidents/export/json", headers=auth_headers(token))
    assert incident_export.status_code == 200, incident_export.text

    dsr = client.post(
        f"/workflows/{org_id}/dsr",
        headers=auth_headers(token),
        json={"request_type": "access", "requester_email": "data.subject@example.com"},
    )
    assert dsr.status_code == 201, dsr.text
    dsr_id = client.get(f"/workflows/{org_id}/dsr", headers=auth_headers(token)).json()[0]["id"]

    dsr_update = client.patch(
        f"/workflows/{org_id}/dsr/{dsr_id}",
        headers=auth_headers(token),
        json={"identity_verified": True, "completion_status": "completed"},
    )
    assert dsr_update.status_code == 200, dsr_update.text
    assert dsr_update.json()["identity_verified"] is True

    dsr_export = client.get(f"/workflows/{org_id}/dsr/export/pdf", headers=auth_headers(token))
    assert dsr_export.status_code == 200, dsr_export.text

    policy = client.post(
        f"/workflows/{org_id}/policies",
        headers=auth_headers(token),
        json={"name": "Information Security Policy", "body_markdown": "Initial draft policy"},
    )
    assert policy.status_code == 201, policy.text
    policy_id = policy.json()["id"]

    policy_update = client.patch(
        f"/workflows/{org_id}/policies/{policy_id}",
        headers=auth_headers(token),
        json={
            "status": "active",
            "visibility": "public",
            "body_markdown": "Approved policy content",
            "is_ai_draft": False,
            "requires_legal_review": True,
        },
    )
    assert policy_update.status_code == 200, policy_update.text

    policy_export = client.get(f"/workflows/{org_id}/policies/export/csv", headers=auth_headers(token))
    assert policy_export.status_code == 200, policy_export.text

    task = client.post(
        f"/workflows/{org_id}/tasks",
        headers=auth_headers(token),
        json={"title": "Close high-risk findings", "description": "Follow remediation plan", "priority": "high"},
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]

    task_update = client.patch(
        f"/workflows/{org_id}/tasks/{task_id}",
        headers=auth_headers(token),
        json={"status": "in_progress", "priority": "medium"},
    )
    assert task_update.status_code == 200, task_update.text
    assert task_update.json()["status"] == "in_progress"

    task_status = client.patch(
        f"/workflows/{org_id}/tasks/{task_id}/status?status_value=done",
        headers=auth_headers(token),
    )
    assert task_status.status_code == 200, task_status.text
    assert task_status.json()["status"] == "done"

    task_export = client.get(f"/workflows/{org_id}/tasks/export/json", headers=auth_headers(token))
    assert task_export.status_code == 200, task_export.text

    delete_calls = [
        client.delete(f"/workflows/{org_id}/tasks/{task_id}", headers=auth_headers(token)),
        client.delete(f"/workflows/{org_id}/policies/{policy_id}", headers=auth_headers(token)),
        client.delete(f"/workflows/{org_id}/dsr/{dsr_id}", headers=auth_headers(token)),
        client.delete(f"/workflows/{org_id}/incidents/{incident_id}", headers=auth_headers(token)),
        client.delete(f"/workflows/{org_id}/vendors/{vendor_id}", headers=auth_headers(token)),
    ]
    for response in delete_calls:
        assert response.status_code == 200, response.text
        assert response.json()["deleted"] is True
