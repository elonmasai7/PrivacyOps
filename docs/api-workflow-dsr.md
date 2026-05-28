# OpenAPI Tag: workflow-dsr

These endpoints are grouped under the `workflow-dsr` OpenAPI tag.

## Endpoints

- `POST /workflows/{organization_id}/dsr`
- `GET /workflows/{organization_id}/dsr`
- `PATCH /workflows/{organization_id}/dsr/{dsr_id}`
- `DELETE /workflows/{organization_id}/dsr/{dsr_id}`
- `GET /workflows/{organization_id}/dsr/export/{export_format}`

## Sample: create DSR

Request:

```json
{
  "request_type": "access",
  "requester_email": "person@example.com",
  "internal_notes": "Submitted via trust center form"
}
```

Response:

```json
{
  "id": "eb003681-5492-42cc-8bc4-a560f37c08a2",
  "organization_id": "e4d8f2be-f801-4ea7-a6d5-0f54558f9e56",
  "request_type": "access",
  "requester_email": "person@example.com",
  "identity_verified": false,
  "due_date": null,
  "assigned_owner_user_id": "27a8cde2-5c27-4ab3-b8e1-a005fa1834f1",
  "internal_notes": "Submitted via trust center form",
  "completion_status": "open",
  "created_at": "2026-05-28T14:30:10.104221",
  "updated_at": "2026-05-28T14:30:10.104227"
}
```

## Sample: verify and complete DSR

Request:

```json
{
  "identity_verified": true,
  "completion_status": "completed",
  "internal_notes": "Response package sent to requester"
}
```

`PATCH /workflows/{organization_id}/dsr/{dsr_id}`

## Sample: list DSR with filters

`GET /workflows/{organization_id}/dsr?request_type=access&completion_status=open&identity_verified=false&limit=50&offset=0`

## Sample: export DSR register

`GET /workflows/{organization_id}/dsr/export/pdf`
