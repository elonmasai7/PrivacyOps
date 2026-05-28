import json

import httpx
import pyotp

from app.config import settings


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def register_user(client, email: str, password: str = "StrongPassword123"):
    response = client.post(
        "/auth/register",
        json={"email": email, "full_name": "Phase One User", "password": password},
    )
    assert response.status_code == 201, response.text


def login_user(client, email: str, password: str = "StrongPassword123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def create_org(client, token: str, slug: str):
    response = client.post(
        "/organizations",
        headers=auth_headers(token),
        json={
            "name": "PhaseOne Org",
            "slug": slug,
            "country": "Kenya",
            "industry": "saas",
            "employee_band": "11-50",
            "revenue_band": "100k-500k",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_mfa_totp_enforced_login_flow(client):
    email = "mfa-user@example.com"
    password = "StrongPassword123"
    register_user(client, email, password)

    first_login = login_user(client, email, password)
    assert first_login.status_code == 200, first_login.text
    access_token = first_login.json()["access_token"]

    begin = client.post("/auth/mfa/setup/begin", headers=auth_headers(access_token))
    assert begin.status_code == 200, begin.text
    setup = begin.json()
    secret = setup["manual_key"]

    code = pyotp.TOTP(secret).now()
    confirm = client.post(
        "/auth/mfa/setup/confirm",
        headers=auth_headers(access_token),
        json={"mfa_code": code},
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["mfa_enabled"] is True

    login_after_mfa = login_user(client, email, password)
    assert login_after_mfa.status_code == 202, login_after_mfa.text
    challenge = login_after_mfa.json()
    assert challenge["requires_mfa"] is True

    verify = client.post(
        "/auth/mfa/verify-login",
        json={"challenge_token": challenge["challenge_token"], "mfa_code": pyotp.TOTP(secret).now()},
    )
    assert verify.status_code == 200, verify.text
    assert "access_token" in verify.json()


def test_oauth_google_start_and_callback(client, monkeypatch):
    settings.oauth_google_client_id = "google-client"
    settings.oauth_google_client_secret = "google-secret"
    settings.oauth_google_redirect_uri = "http://localhost:3000/oauth/google/callback"

    start = client.get("/auth/oauth/google/start")
    assert start.status_code == 200, start.text
    assert start.json()["status"] == "configured"
    assert "authorization_url" in start.json()

    class FakeResponse:
        def __init__(self, status_code: int, payload: dict):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, data=None):
            return FakeResponse(200, {"access_token": "oauth-token"})

        async def get(self, url, headers=None):
            return FakeResponse(200, {"sub": "google-subject-1", "email": "oauth-user@example.com", "name": "OAuth User"})

    monkeypatch.setattr("app.routers.auth.httpx.AsyncClient", lambda timeout=20: FakeAsyncClient())

    callback = client.post(
        "/auth/oauth/callback",
        json={"provider": "google", "code": "auth-code", "redirect_uri": settings.oauth_google_redirect_uri},
    )
    assert callback.status_code == 200, callback.text
    assert "access_token" in callback.json()


def test_stripe_checkout_and_webhook_subscription_sync(client, monkeypatch):
    settings.stripe_secret_key = "sk_test_key"
    settings.stripe_webhook_secret = "whsec_test"
    settings.stripe_price_starter = "price_starter"

    register_user(client, "billing-owner@example.com")
    login = login_user(client, "billing-owner@example.com")
    token = login.json()["access_token"]
    org_id = create_org(client, token, "billing-phase1")

    monkeypatch.setattr("app.routers.billing.stripe.Customer.create", lambda **kwargs: {"id": "cus_123"})
    monkeypatch.setattr(
        "app.routers.billing.stripe.checkout.Session.create",
        lambda **kwargs: {"id": "cs_123", "url": "https://checkout.stripe.example/session"},
    )

    checkout = client.post(
        f"/billing/{org_id}/checkout-session",
        headers=auth_headers(token),
        json={
            "plan_name": "starter",
            "success_url": "http://localhost:3000/success",
            "cancel_url": "http://localhost:3000/cancel",
        },
    )
    assert checkout.status_code == 200, checkout.text
    assert checkout.json()["session_id"] == "cs_123"

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_123",
                "subscription": "sub_123",
                "metadata": {"organization_id": org_id, "plan_name": "starter"},
            }
        },
    }
    monkeypatch.setattr("app.routers.billing.stripe.Webhook.construct_event", lambda payload, sig_header, secret: event)

    webhook = client.post(
        "/billing/webhook",
        data=json.dumps({"event": "test"}),
        headers={"stripe-signature": "sig"},
    )
    assert webhook.status_code == 200, webhook.text
    assert webhook.json()["received"] is True

    billing_state = client.get(f"/billing/{org_id}", headers=auth_headers(token))
    assert billing_state.status_code == 200, billing_state.text
    assert billing_state.json()["subscription"]["state"] in {"active", "none"}


def test_aws_connect_and_sync_baseline(client, monkeypatch):
    register_user(client, "aws-owner@example.com")
    login = login_user(client, "aws-owner@example.com")
    token = login.json()["access_token"]
    org_id = create_org(client, token, "aws-phase1")

    monkeypatch.setattr(
        "app.routers.integrations.validate_aws_credentials",
        lambda config: {"account": "123456789012", "arn": "arn:aws:iam::123456789012:user/test"},
    )

    connect = client.post(
        f"/integrations/{org_id}/connect",
        headers=auth_headers(token),
        json={
            "provider": "aws",
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_region": "us-east-1",
        },
    )
    assert connect.status_code == 201, connect.text
    assert connect.json()["provider"] == "aws"

    monkeypatch.setattr("app.routers.integrations.scan_aws", lambda integration, db: [])
    sync = client.post(f"/integrations/{org_id}/aws/sync", headers=auth_headers(token))
    assert sync.status_code == 200, sync.text
    assert isinstance(sync.json(), list)


def test_gitlab_connect_and_sync_baseline(client, monkeypatch):
    register_user(client, "gitlab-owner@example.com")
    login = login_user(client, "gitlab-owner@example.com")
    token = login.json()["access_token"]
    org_id = create_org(client, token, "gitlab-phase1")

    class FakeResponse:
        def __init__(self, status_code: int, payload: dict | list):
            self.status_code = status_code
            self._payload = payload
            self.request = httpx.Request("GET", "https://example.test")

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("error", request=self.request, response=httpx.Response(self.status_code, request=self.request))

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None, params=None):
            if url.endswith("/user"):
                return FakeResponse(200, {"id": 123, "username": "gitlab-user"})
            if url.endswith("/projects"):
                return FakeResponse(200, [{"id": 1, "path_with_namespace": "acme/core", "visibility": "public", "default_branch": "main"}])
            if "/protected_branches/" in url:
                return FakeResponse(404, {"message": "404"})
            if url.endswith("/approvals"):
                return FakeResponse(200, {"approvals_before_merge": 0})
            return FakeResponse(200, {})

    monkeypatch.setattr("app.routers.integrations.httpx.AsyncClient", lambda timeout=20: FakeAsyncClient())
    monkeypatch.setattr("app.services.httpx.AsyncClient", lambda timeout=30: FakeAsyncClient())

    connect = client.post(
        f"/integrations/{org_id}/connect",
        headers=auth_headers(token),
        json={
            "provider": "gitlab",
            "personal_access_token": "glpat-validtoken123456",
        },
    )
    assert connect.status_code == 201, connect.text
    assert connect.json()["provider"] == "gitlab"

    sync = client.post(f"/integrations/{org_id}/gitlab/sync", headers=auth_headers(token))
    assert sync.status_code == 200, sync.text
    data = sync.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_framework_pack_import_export_and_review(client):
    register_user(client, "framework-owner@example.com")
    login = login_user(client, "framework-owner@example.com")
    token = login.json()["access_token"]
    org_id = create_org(client, token, "framework-pack-org")

    imported = client.post(
        f"/frameworks/{org_id}/packs/import",
        headers=auth_headers(token),
        json={
            "name": "Kenya DPA Community Pack",
            "jurisdiction": "Kenya",
            "source_reference": "https://www.odpc.go.ke/",
            "status": "active",
            "version": "2026.05",
            "review_status": "community-reviewed",
            "controls": [
                {
                    "category": "accountability",
                    "title": "Data controller registration readiness",
                    "requirement_text": "Organization should maintain ODPC registration evidence where applicable.",
                    "evidence_expectation": "ODPC registration records",
                    "risk_weight": 3,
                    "mappings": {"gdpr": ["Art. 30"]},
                }
            ],
        },
    )
    assert imported.status_code == 201, imported.text
    framework_id = imported.json()["framework_id"]

    exported = client.get(f"/frameworks/{org_id}/{framework_id}/packs/export", headers=auth_headers(token))
    assert exported.status_code == 200, exported.text
    payload = exported.json()
    assert payload["framework"]["name"] == "Kenya DPA Community Pack"
    assert payload["version"]["review_status"] == "community-reviewed"
    assert len(payload["controls"]) == 1

    review = client.patch(
        f"/frameworks/{org_id}/versions/{payload['version']['id']}/review",
        headers=auth_headers(token),
        json={"review_status": "expert-reviewed", "reviewer_notes": "Independent reviewer sign-off complete"},
    )
    assert review.status_code == 200, review.text
    assert review.json()["review_status"] == "expert-reviewed"


def test_admin_ai_setting_gates_assistant(client):
    register_user(client, "assistant-owner@example.com")
    login = login_user(client, "assistant-owner@example.com")
    token = login.json()["access_token"]
    org_id = create_org(client, token, "assistant-org")

    blocked = client.post(
        f"/assistant/{org_id}",
        headers=auth_headers(token),
        json={"prompt": "Summarize my compliance gaps for GDPR readiness.", "context": {}},
    )
    assert blocked.status_code == 403, blocked.text

    setting = client.put(
        f"/admin/{org_id}/settings",
        headers=auth_headers(token),
        json={"key": "ai_assistant_enabled", "value": "true"},
    )
    assert setting.status_code == 201, setting.text

    allowed = client.post(
        f"/assistant/{org_id}",
        headers=auth_headers(token),
        json={"prompt": "Summarize my compliance gaps for GDPR readiness.", "context": {}},
    )
    assert allowed.status_code == 200, allowed.text
    assert "confidence_level" in allowed.json()
