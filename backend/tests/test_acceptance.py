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
