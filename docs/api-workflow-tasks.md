# OpenAPI Tag: workflow-tasks

These endpoints are grouped under the `workflow-tasks` OpenAPI tag.

## Endpoints

- `POST /workflows/{organization_id}/tasks`
- `GET /workflows/{organization_id}/tasks`
- `PATCH /workflows/{organization_id}/tasks/{task_id}`
- `PATCH /workflows/{organization_id}/tasks/{task_id}/status`
- `DELETE /workflows/{organization_id}/tasks/{task_id}`
- `GET /workflows/{organization_id}/tasks/export/{export_format}`

## Sample: create task

Request:

```json
{
  "title": "Attach evidence for access control review",
  "description": "Map IAM review file to SOC2 control AC-01",
  "priority": "high"
}
```

Response:

```json
{
  "id": "809feeb3-f8f9-4c06-bb45-61e0ddb1f0cb",
  "organization_id": "e4d8f2be-f801-4ea7-a6d5-0f54558f9e56",
  "title": "Attach evidence for access control review",
  "description": "Map IAM review file to SOC2 control AC-01",
  "assignee_user_id": "27a8cde2-5c27-4ab3-b8e1-a005fa1834f1",
  "due_date": null,
  "priority": "high",
  "status": "open",
  "framework_id": null,
  "control_id": null,
  "created_at": "2026-05-28T14:34:41.112115",
  "updated_at": "2026-05-28T14:34:41.112120"
}
```

## Sample: update task body

`PATCH /workflows/{organization_id}/tasks/{task_id}`

```json
{
  "status": "in_progress",
  "priority": "medium",
  "description": "Evidence uploaded, awaiting reviewer approval"
}
```

## Sample: quick status update

`PATCH /workflows/{organization_id}/tasks/{task_id}/status?status_value=done`

Response:

```json
{
  "id": "809feeb3-f8f9-4c06-bb45-61e0ddb1f0cb",
  "status": "done"
}
```

## Sample: list and export

- List with filters: `GET /workflows/{organization_id}/tasks?status=open&priority=high&query=evidence`
- Export: `GET /workflows/{organization_id}/tasks/export/json`
