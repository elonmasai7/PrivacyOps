# OpenAPI Tag: workflow-policies

These endpoints are grouped under the `workflow-policies` OpenAPI tag.

## Endpoints

- `POST /workflows/{organization_id}/policies`
- `GET /workflows/{organization_id}/policies`
- `PATCH /workflows/{organization_id}/policies/{policy_id}`
- `DELETE /workflows/{organization_id}/policies/{policy_id}`
- `GET /workflows/{organization_id}/policies/export/{export_format}`

## Sample: create policy

Request:

```json
{
  "name": "Information Security Policy",
  "body_markdown": "# Information Security Policy\n\nInitial policy draft."
}
```

Response:

```json
{
  "id": "f5e56f31-aaf6-45b2-a89a-7f2fc9ef9d54",
  "name": "Information Security Policy",
  "status": "draft",
  "requires_legal_review": true
}
```

## Sample: publish policy and create a new version

Request:

```json
{
  "status": "active",
  "visibility": "public",
  "body_markdown": "# Information Security Policy\n\nApproved content v2.",
  "is_ai_draft": false,
  "requires_legal_review": true
}
```

`PATCH /workflows/{organization_id}/policies/{policy_id}`

When `body_markdown` is provided, a new `policy_versions` row is created automatically.

## Sample: list policies with filters

`GET /workflows/{organization_id}/policies?status=active&visibility=public&limit=100&offset=0`

## Sample: export policy inventory

`GET /workflows/{organization_id}/policies/export/csv`
