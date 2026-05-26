# Compliance Framework Management Guide

## Purpose

Framework management ensures legal and audit content is versioned, reviewable, and traceable without hardcoding static logic into the UI.

## Data Model

- `frameworks`: top-level framework identity and lifecycle status.
- `framework_versions`: version snapshots and reviewer metadata.
- `controls`: control statements and evidence expectations.
- `requirements`: requirement decomposition for implementation tracking.
- `control_mappings`: cross-framework control mapping.

## Lifecycle

1. Create framework record with jurisdiction and source reference.
2. Create initial version.
3. Add categories, controls, and requirements.
4. Review content with compliance/legal experts.
5. Activate when approved.
6. Archive superseded versions without deleting historical trace.

## Governance Rules

- Every update should capture reviewer identity and review date.
- Changelog should explain why a change happened.
- Status should flow through `draft` -> `active` -> `archived`.
- Legal-sensitive interpretation must be marked for legal review.

## Operational Guidance

- Keep source references to regulator or standards material.
- Use mapping records to reduce duplicate control implementation across Kenya DPA, GDPR, SOC 2, and ISO 27001 readiness.
- Treat framework content as operational guidance until legally approved.
