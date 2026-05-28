# OpenAPI Tag: workflow-incidents

These endpoints are grouped under the `workflow-incidents` OpenAPI tag.

## Endpoints

- `POST /workflows/{organization_id}/incidents`
- `GET /workflows/{organization_id}/incidents`
- `PATCH /workflows/{organization_id}/incidents/{incident_id}`
- `DELETE /workflows/{organization_id}/incidents/{incident_id}`
- `GET /workflows/{organization_id}/incidents/export/{export_format}`

## Sample: create incident

Request:

```json
{
  "title": "Credential stuffing attempt on customer portal",
  "severity": "high",
  "affected_systems": ["auth-api", "customer-portal"],
  "affected_data_subjects": 14,
  "affected_data_categories": ["email", "phone"],
  "root_cause": "Password reuse by users",
  "risk_of_harm": "Potential account takeover"
}
```

Response:

```json
{
  "id": "499d53bc-f2ab-4e66-a8fa-1fdfa4eb06a5",
  "organization_id": "e4d8f2be-f801-4ea7-a6d5-0f54558f9e56",
  "title": "Credential stuffing attempt on customer portal",
  "severity": "high",
  "affected_systems": ["auth-api", "customer-portal"],
  "affected_data_subjects": 14,
  "affected_data_categories": ["email", "phone"],
  "timeline": {"created_at": "2026-05-28T14:26:33.114012"},
  "root_cause": "Password reuse by users",
  "risk_of_harm": "Potential account takeover",
  "status": "open",
  "breach_clock_started_at": "2026-05-28T14:26:33.113992",
  "created_at": "2026-05-28T14:26:33.115220",
  "updated_at": "2026-05-28T14:26:33.115229"
}
```

## Sample: list incidents with filters

`GET /workflows/{organization_id}/incidents?query=portal&severity=high&status=open&limit=100&offset=0`

## Sample: close incident

Request:

```json
{
  "status": "closed",
  "root_cause": "Mitigated with additional bot controls"
}
```

`PATCH /workflows/{organization_id}/incidents/{incident_id}`

## Sample: export incidents

`GET /workflows/{organization_id}/incidents/export/json`
