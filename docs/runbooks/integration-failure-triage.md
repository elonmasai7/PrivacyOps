# Integration Failure Triage Runbook

## Purpose

Standardize investigation and recovery when an integration sync fails or connector health degrades.

## Scope

- GitHub connector (implemented)
- Future connectors: AWS, GitLab, Google Workspace, Microsoft Graph, Cloudflare, Jira, Linear, Sentry, Slack

## Detection Signals

- Integration status becomes `error`.
- `last_error` field populated.
- Scheduled/manual sync returns non-2xx.
- Expected findings/evidence stop updating.

## Triage Steps

1. **Confirm failure context**
   - Identify organization and provider.
   - Capture timestamp and user/action that triggered failure.
2. **Classify issue type**
   - Credential/token expired or revoked.
   - Permission scope insufficient.
   - External API outage/rate limit.
   - Internal parsing or mapping failure.
3. **Inspect artifacts**
   - Review integration record: status, `last_synced_at`, `last_error`.
   - Review recent audit logs for integration actions.
4. **Recover**
   - Reconnect token with least-privilege required scopes.
   - Re-run sync.
   - Validate new findings/evidence output.
5. **Escalate if unresolved**
   - Open engineering task with failure details.
   - Attach request/response metadata and reproduction steps.

## GitHub-Specific Checks

- Token still valid for `/user` endpoint.
- Token has repository visibility access for target org/repos.
- API limits not exhausted.
- Default branch fetch endpoints return expected payloads.

## Manual Fallback

If connector cannot be restored immediately:

- Switch to manual evidence collection for impacted controls.
- Record fallback decision in audit trail.
- Set reminder task to restore automation coverage.

## Exit Criteria

- Connector status is `connected`.
- Sync succeeds and `last_synced_at` updates.
- Findings/evidence refresh verified.
