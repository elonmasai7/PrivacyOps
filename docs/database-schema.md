# Database Schema Documentation

Primary entities include:

- Identity and tenancy: `users`, `organizations`, `memberships`, `roles`, `permissions`
- Frameworks: `frameworks`, `framework_versions`, `control_categories`, `controls`, `requirements`, `control_mappings`
- Assessments: `assessments`, `assessment_answers`, `dpias`, `dpia_answers`
- Data governance: `processing_activities`, `data_categories`, `data_subject_categories`, `lawful_bases`
- Evidence/reporting: `files`, `evidence`, `evidence_versions`, `reports`, `report_exports`
- Risk workflows: `vendors`, `vendor_reviews`, `incidents`, `breach_assessments`, `data_subject_requests`
- Policy and trust: `policies`, `policy_versions`, `policy_acknowledgements`, `trust_center_pages`, `trust_center_documents`
- Integrations/security: `integrations`, `integration_tokens`, `security_findings`
- Operations: `tasks`, `notifications`, `billing_customers`, `subscriptions`, `audit_logs`

All tenant-owned entities include `organization_id` and are guarded in API logic.
