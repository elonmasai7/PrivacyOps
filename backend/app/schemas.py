from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models import RoleName


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=10, max_length=128)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class MFALoginVerifyRequest(BaseModel):
    challenge_token: str
    mfa_code: str = Field(min_length=6, max_length=8)


class LoginChallengeResponse(BaseModel):
    requires_mfa: bool = True
    challenge_token: str
    challenge_type: str = "totp"
    expires_in_seconds: int


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    mfa_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OAuthStartResponse(BaseModel):
    provider: str
    authorization_url: str | None
    status: str
    setup_instructions: str | None = None


class OAuthCallbackRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: str | None = None


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(pattern=r"^[a-z0-9-]{3,60}$")
    country: str = Field(min_length=2, max_length=80)
    industry: str | None = None
    employee_band: str | None = None
    revenue_band: str | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    country: str
    industry: str | None
    onboarding_completed: bool
    trust_readiness_score: int
    privacy_health_map: dict[str, Any]

    class Config:
        from_attributes = True


class MembershipResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role: RoleName

    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: RoleName


class MemberProfileResponse(BaseModel):
    membership_id: str
    user_id: str
    email: EmailStr
    full_name: str
    role: RoleName


class OnboardingAnswersRequest(BaseModel):
    answers: dict[str, Any]


class OnboardingResultResponse(BaseModel):
    trust_readiness_score: int
    suggested_frameworks: list[str]
    required_workflows: list[str]
    risk_areas: list[str]
    recommended_next_actions: list[str]
    missing_evidence: list[str]


class ProcessingActivityCreateRequest(BaseModel):
    name: str
    data_categories: list[str]
    data_subject_categories: list[str]
    purpose: str
    lawful_basis: str
    system_name: str
    data_location: str
    vendor_name: str | None = None
    retention_period: str
    security_measures: str
    cross_border_transfer: bool = False
    risk_level: str
    review_date: datetime | None = None


class ProcessingActivityResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    lawful_basis: str
    risk_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    source: str
    collection_method: str
    review_status: str
    approval_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCreateRequest(BaseModel):
    report_type: str
    framework: str


class ReportResponse(BaseModel):
    id: str
    organization_id: str
    report_type: str
    framework: str
    score: int
    payload: dict[str, Any]
    version_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class FrameworkCreateRequest(BaseModel):
    name: str
    jurisdiction: str
    source_reference: str | None = None
    status: str


class FrameworkResponse(BaseModel):
    id: str
    name: str
    jurisdiction: str
    source_reference: str | None
    status: str

    class Config:
        from_attributes = True


class IntegrationConnectRequest(BaseModel):
    provider: str
    personal_access_token: str | None = Field(default=None, min_length=10, max_length=255)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None
    aws_region: str | None = None


class IntegrationResponse(BaseModel):
    id: str
    organization_id: str
    provider: str
    status: str
    last_synced_at: datetime | None
    last_error: str | None

    class Config:
        from_attributes = True


class SecurityFindingResponse(BaseModel):
    id: str
    title: str
    severity: str
    category: str
    status: str
    details: dict[str, Any]

    class Config:
        from_attributes = True


class AIRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=8000)
    context: dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    guidance: str
    confidence_level: str
    requires_legal_review: bool
    source_references: list[str]
    next_action: str


class MFASetupBeginResponse(BaseModel):
    otp_auth_uri: str
    manual_key: str
    app_name: str


class MFASetupConfirmRequest(BaseModel):
    mfa_code: str = Field(min_length=6, max_length=8)


class CheckoutSessionRequest(BaseModel):
    plan_name: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
