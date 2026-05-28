# Framework Pack Guide

Framework packs let organizations import and version compliance controls without hardcoding framework logic into frontend pages.

## Review status values

- `unverified`
- `community-reviewed`
- `expert-reviewed`

## Import endpoint

`POST /frameworks/{organization_id}/packs/import`

Example payload:

```json
{
  "name": "Kenya DPA Pack",
  "jurisdiction": "Kenya",
  "source_reference": "https://www.odpc.go.ke/",
  "status": "active",
  "version": "2026.05",
  "review_status": "community-reviewed",
  "reviewer_notes": "Mapped by contributors",
  "controls": [
    {
      "category": "accountability",
      "title": "Controller readiness",
      "requirement_text": "Document controller obligations",
      "evidence_expectation": "Policy and process records",
      "risk_weight": 3,
      "mappings": {
        "gdpr": ["Art. 30"]
      }
    }
  ]
}
```

## Export endpoint

`GET /frameworks/{organization_id}/{framework_id}/packs/export`

Returns framework metadata, selected version metadata, and control definitions.

## Review update endpoint

`PATCH /frameworks/{organization_id}/versions/{version_id}/review`

Use this endpoint to move a version between review states with reviewer notes.
