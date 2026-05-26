# Integration Setup Guide

## Integration Philosophy

- Use real APIs where connector exists.
- If a connector is not yet automated, use manual evidence workflow.
- Never fabricate scan output or integration states.

## GitHub Integration (Implemented)

### Required token scope

Use a GitHub PAT with least-privilege read access needed for repository metadata and branch checks.

### Setup steps

1. Open workspace module: `Integrations`.
2. Enter PAT in the connect form.
3. Submit connection (`POST /integrations/{organization_id}/connect`).
4. Run sync (`POST /integrations/{organization_id}/github/sync`).
5. Review findings (`GET /integrations/{organization_id}/findings`).

### Findings currently collected

- Public repository visibility.
- Branch protection absent on default branch.

## Provider States

Integration state endpoint: `GET /security-posture/{organization_id}/integrations-state`

- `connected`: provider connected and sync-capable.
- `not_connected`: setup required.
- `error`: last sync or validation failed.

## Manual Evidence Fallback

For non-automated providers (AWS, GitLab, Google Workspace, Microsoft Graph, Cloudflare, Jira, Linear, Sentry, Slack):

- collect screenshots or config exports,
- upload to Evidence Vault,
- map evidence to controls,
- track review and expiry.
