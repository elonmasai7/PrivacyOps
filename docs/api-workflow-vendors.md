# OpenAPI Tag: workflow-vendors

These endpoints are grouped under the `workflow-vendors` OpenAPI tag.

## Endpoints

- `POST /workflows/{organization_id}/vendors`
- `GET /workflows/{organization_id}/vendors`
- `PATCH /workflows/{organization_id}/vendors/{vendor_id}`
- `DELETE /workflows/{organization_id}/vendors/{vendor_id}`
- `GET /workflows/{organization_id}/vendors/export/{export_format}`

## Sample: create vendor

Request:

```json
{
  "name": "Safiri Cloud",
  "service_provided": "Managed Kubernetes hosting",
  "data_processed": "Customer account metadata",
  "country": "Kenya",
  "subprocessors": ["BackupOps Kenya"],
  "contract_status": "active",
  "dpa_status": "signed",
  "security_review_status": "passed",
  "risk_level": "medium",
  "notes": "Annual reassessment due in Q4"
}
```

Response:

```json
{
  "id": "9d32d97e-42d3-45a3-8c8d-6d35f6f307b2",
  "organization_id": "e4d8f2be-f801-4ea7-a6d5-0f54558f9e56",
  "name": "Safiri Cloud",
  "service_provided": "Managed Kubernetes hosting",
  "data_processed": "Customer account metadata",
  "country": "Kenya",
  "subprocessors": ["BackupOps Kenya"],
  "contract_status": "active",
  "dpa_status": "signed",
  "security_review_status": "passed",
  "risk_level": "medium",
  "renewal_date": null,
  "owner_user_id": "27a8cde2-5c27-4ab3-b8e1-a005fa1834f1",
  "notes": "Annual reassessment due in Q4",
  "created_at": "2026-05-28T14:25:00.019102",
  "updated_at": "2026-05-28T14:25:00.019112"
}
```

## Sample: list vendors with filters

`GET /workflows/{organization_id}/vendors?query=cloud&risk_level=high&sort_by=created_at&sort_order=desc&limit=50&offset=0`

## Sample: export vendors

`GET /workflows/{organization_id}/vendors/export/csv`

Supported `export_format` values:

- `csv`
- `json`
- `pdf`
