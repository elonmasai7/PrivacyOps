# Incident Response Runbook

## Purpose

Provide a standard response flow for security incidents and privacy breaches, including legal/compliance coordination and customer communication readiness.

## Severity Levels

- `low`: limited impact, no sensitive data exposure.
- `medium`: internal disruption or potential limited data exposure.
- `high`: confirmed breach or major service/security impact.
- `critical`: active incident with significant data subject or regulatory risk.

## Trigger Conditions

- Security finding indicates active compromise.
- Unauthorized access detected.
- Data exfiltration suspected or confirmed.
- Privacy complaint indicates rights handling failure.

## Response Workflow

1. **Detect and declare**
   - Create incident record in `Incidents` module.
   - Assign incident commander and compliance owner.
2. **Contain**
   - Isolate affected systems/accounts.
   - Rotate potentially exposed credentials/tokens.
3. **Assess impact**
   - Identify affected systems and data categories.
   - Estimate affected data subjects.
   - Document timeline and root-cause hypotheses.
4. **Regulatory readiness**
   - Start breach clock if applicable.
   - Prepare regulator notification checklist.
   - Mark legal-sensitive outputs as requiring legal review.
5. **Communicate**
   - Draft internal status updates.
   - Prepare customer-facing statement only after legal/compliance review.
6. **Recover**
   - Restore secure operations.
   - Validate controls and close containment gaps.
7. **Post-incident review**
   - Complete root cause and corrective actions.
   - Convert actions into tracked tasks with owners and due dates.

## Required Evidence

- Detection logs and timestamps
- Incident timeline records
- Access and change logs
- Notification drafts and approvals
- Remediation evidence and verification steps

## Exit Criteria

- Incident status moved to closed with documented root cause.
- Corrective tasks created and assigned.
- Audit log reflects major response actions.
