# CivicLens Lemma Pod

Import this pod after creating a Lemma pod shell:

```bash
lemma pods create civic-lens --org <your-org>
lemma pods import ./pod/civic-lens --dry-run
lemma pods import ./pod/civic-lens
lemma records import departments ./pod/civic-lens/seed/departments.json
lemma files upload ./pod/civic-lens/files/knowledge/municipal-departments.md /knowledge/municipal-departments.md
```

## Resources

| Resource | Name |
|----------|------|
| Tables | `petitions`, `departments`, `activity_log` |
| Agents | `issue-classifier`, `complaint-drafter`, `resolution-checker` |
| Functions | `create_petition`, `send_complaint_email`, `escalate_petition`, `update_resolution_status` |
| Workflows | `petition-pipeline`, `escalation-pipeline` |
| Schedule | `daily-resolution-check` (9am daily → escalation-pipeline) |

## Smoke test

```bash
lemma workflows run petition-pipeline --data '{
  "photo_url": "https://example.com/pothole.jpg",
  "description": "Large pothole on Main Street",
  "address": "123 Main St, Metro City",
  "lat": 12.9716,
  "lng": 77.5946
}'
# When workflow pauses at approval form:
lemma workflows runs waiting
lemma workflows runs submit-form <run-id> --data '{"approved": true, "subject": "...", "body": "..."}'
```

## Environment (functions)

Set on the Lemma pod runtime:
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- `DEMO_EMAIL_TO` (fallback recipient)
- `ESCALATION_DAYS` (default: 3)
