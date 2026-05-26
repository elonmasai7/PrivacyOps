import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _id() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RoleName(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    compliance_manager = "compliance_manager"
    security_manager = "security_manager"
    legal_advisor = "legal_advisor"
    auditor = "auditor"
    member = "member"
    viewer = "viewer"
    trust_center_guest = "trust_center_guest"


class FrameworkStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class RecordStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class IntegrationProvider(str, enum.Enum):
    github = "github"
    gitlab = "gitlab"
    aws = "aws"
    google_workspace = "google_workspace"
    microsoft_graph = "microsoft_graph"
    cloudflare = "cloudflare"
    slack = "slack"
    jira = "jira"
    linear = "linear"
    sentry = "sentry"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    industry: Mapped[str] = mapped_column(String(120), nullable=True)
    employee_band: Mapped[str] = mapped_column(String(80), nullable=True)
    revenue_band: Mapped[str] = mapped_column(String(80), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trust_readiness_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    privacy_health_map: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="organization")


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[RoleName] = mapped_column(Enum(RoleName), nullable=False)

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="memberships")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str] = mapped_column(String(120), nullable=False)
    target_id: Mapped[str] = mapped_column(String(120), nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Framework(Base, TimestampMixin):
    __tablename__ = "frameworks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(120), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[FrameworkStatus] = mapped_column(Enum(FrameworkStatus), default=FrameworkStatus.draft, nullable=False)


class FrameworkVersion(Base, TimestampMixin):
    __tablename__ = "framework_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    framework_id: Mapped[str] = mapped_column(ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    changelog: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Control(Base, TimestampMixin):
    __tablename__ = "controls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    framework_version_id: Mapped[str] = mapped_column(ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_expectation: Mapped[str] = mapped_column(Text, nullable=True)
    risk_weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    mappings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    framework_version_id: Mapped[str] = mapped_column(ForeignKey("framework_versions.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus), default=RecordStatus.draft, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    findings_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class AssessmentAnswer(Base, TimestampMixin):
    __tablename__ = "assessment_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_key: Mapped[str] = mapped_column(String(120), nullable=False)
    answer_value: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ProcessingActivity(Base, TimestampMixin):
    __tablename__ = "processing_activities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_categories: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    data_subject_categories: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    lawful_basis: Mapped[str] = mapped_column(String(120), nullable=False)
    system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_location: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=True)
    retention_period: Mapped[str] = mapped_column(String(120), nullable=False)
    security_measures: Mapped[str] = mapped_column(Text, nullable=False)
    cross_border_transfer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    review_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    framework_id: Mapped[str] = mapped_column(ForeignKey("frameworks.id", ondelete="SET NULL"), nullable=True)
    control_id: Mapped[str] = mapped_column(ForeignKey("controls.id", ondelete="SET NULL"), nullable=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    collection_method: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    expiry_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    review_status: Mapped[str] = mapped_column(String(60), nullable=False, default="pending")
    approval_status: Mapped[str] = mapped_column(String(60), nullable=False, default="pending")


class EvidenceVersion(Base):
    __tablename__ = "evidence_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_provided: Mapped[str] = mapped_column(Text, nullable=False)
    data_processed: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    subprocessors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    contract_status: Mapped[str] = mapped_column(String(80), nullable=False)
    dpa_status: Mapped[str] = mapped_column(String(80), nullable=False)
    security_review_status: Mapped[str] = mapped_column(String(80), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(60), nullable=False)
    renewal_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    affected_systems: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    affected_data_subjects: Mapped[int] = mapped_column(Integer, nullable=True)
    affected_data_categories: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    timeline: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=True)
    risk_of_harm: Mapped[str] = mapped_column(Text, nullable=True)
    breach_clock_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(80), default="open", nullable=False)


class DataSubjectRequest(Base, TimestampMixin):
    __tablename__ = "data_subject_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    request_type: Mapped[str] = mapped_column(String(80), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(320), nullable=False)
    identity_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    assigned_owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    internal_notes: Mapped[str] = mapped_column(Text, nullable=True)
    completion_status: Mapped[str] = mapped_column(String(80), default="open", nullable=False)


class Policy(Base, TimestampMixin):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus), default=RecordStatus.draft, nullable=False)
    effective_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    review_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    visibility: Mapped[str] = mapped_column(String(40), default="private", nullable=False)


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    version_label: Mapped[str] = mapped_column(String(40), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    is_ai_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_legal_review: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    framework: Mapped[str] = mapped_column(String(120), nullable=False)
    report_type: Mapped[str] = mapped_column(String(120), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generated_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class ReportExport(Base):
    __tablename__ = "report_exports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    export_format: Mapped[str] = mapped_column(String(20), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Integration(Base, TimestampMixin):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(Enum(IntegrationProvider), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="disconnected", nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)


class IntegrationToken(Base):
    __tablename__ = "integration_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    token_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SecurityFinding(Base, TimestampMixin):
    __tablename__ = "security_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(40), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    evidence_ref: Mapped[str] = mapped_column(String(255), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    assignee_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    framework_id: Mapped[str] = mapped_column(ForeignKey("frameworks.id", ondelete="SET NULL"), nullable=True)
    control_id: Mapped[str] = mapped_column(ForeignKey("controls.id", ondelete="SET NULL"), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class TrustCenterPage(Base, TimestampMixin):
    __tablename__ = "trust_center_pages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)


class TrustCenterDocument(Base, TimestampMixin):
    __tablename__ = "trust_center_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visibility: Mapped[str] = mapped_column(String(40), default="private", nullable=False)


class BillingCustomer(Base, TimestampMixin):
    __tablename__ = "billing_customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, default="stripe")
    provider_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    plan_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(80), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class ControlCategory(Base):
    __tablename__ = "control_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    framework_version_id: Mapped[str] = mapped_column(ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    control_id: Mapped[str] = mapped_column(ForeignKey("controls.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class ControlMapping(Base):
    __tablename__ = "control_mappings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    source_control_id: Mapped[str] = mapped_column(ForeignKey("controls.id", ondelete="CASCADE"), nullable=False)
    target_framework_id: Mapped[str] = mapped_column(ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False)
    target_control_ref: Mapped[str] = mapped_column(String(120), nullable=False)


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DataCategory(Base):
    __tablename__ = "data_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class DataSubjectCategory(Base):
    __tablename__ = "data_subject_categories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class LawfulBasis(Base):
    __tablename__ = "lawful_bases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class Dpia(Base, TimestampMixin):
    __tablename__ = "dpias"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    screening_result: Mapped[str] = mapped_column(String(80), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mitigation_plan: Mapped[str] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)


class DpiaAnswer(Base):
    __tablename__ = "dpia_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    dpia_id: Mapped[str] = mapped_column(ForeignKey("dpias.id", ondelete="CASCADE"), nullable=False)
    question_key: Mapped[str] = mapped_column(String(120), nullable=False)
    answer_value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class VendorReview(Base, TimestampMixin):
    __tablename__ = "vendor_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    reviewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)


class BreachAssessment(Base, TimestampMixin):
    __tablename__ = "breach_assessments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    regulator_notification_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_notification_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deadline_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class PolicyAcknowledgement(Base):
    __tablename__ = "policy_acknowledgements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    policy_id: Mapped[str] = mapped_column(ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
