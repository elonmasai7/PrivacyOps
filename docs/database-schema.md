# Database Schema Documentation

## Design Principles

- Organization-first tenancy model.
- Clear domain tables per module to avoid overloaded generic records.
- Versionable artifacts (frameworks, evidence, policies, reports).
- Auditability for security-sensitive operations.

## Identity and Tenancy

- `users`: account identity, profile, auth state.
- `organizations`: tenant root and onboarding score state.
- `memberships`: user-to-organization relationship and role assignment.
- `roles`, `permissions`: extensibility for fine-grained authorization expansion.

## Framework and Control Registry

- `frameworks`: framework records with status/jurisdiction/source.
- `framework_versions`: immutable version snapshots and reviewer metadata.
- `control_categories`: grouped control domains.
- `controls`: detailed controls with requirement/evidence/risk weight.
- `requirements`: sub-requirement decomposition.
- `control_mappings`: cross-framework mapping records.

## Assessments and Readiness

- `assessments`, `assessment_answers`: questionnaire response storage.
- `dpias`, `dpia_answers`: DPIA workflow, screening, and answer traceability.

## Data Governance

- `processing_activities`: RoPA backbone entity.
- `data_categories`, `data_subject_categories`, `lawful_bases`: governance metadata catalogs.

## Evidence and Reporting

- `files`: file metadata store.
- `evidence`: mapped evidence records per framework/control.
- `evidence_versions`: evidence revision history.
- `reports`: generated report payloads and score snapshots.
- `report_exports`: export artifact tracking.

## Risk and Incident Operations

- `vendors`, `vendor_reviews`: third-party governance.
- `incidents`, `breach_assessments`: incident lifecycle and breach readiness.
- `data_subject_requests`: rights request handling.

## Policies and Trust Center

- `policies`, `policy_versions`, `policy_acknowledgements`: policy lifecycle and employee attestation.
- `trust_center_pages`, `trust_center_documents`: customer-facing trust publication records.

## Security Integrations and Findings

- `integrations`: provider connection state.
- `integration_tokens`: token references/scopes.
- `security_findings`: normalized finding records for posture analysis.

## Operations and Billing

- `tasks`, `notifications`: action tracking and user communication.
- `billing_customers`, `subscriptions`: billing state linkage.
- `audit_logs`: immutable action trail with actor/target context.

## Tenancy Enforcement

All tenant-owned entities use `organization_id` and are protected through API membership checks and role checks before read/write operations.
