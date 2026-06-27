# Urbis API Reference

Base URL: `http://localhost:8000` (development) or your Render API URL (production).

All authenticated endpoints use HTTP-only session cookies (`credentials: include`).

---

## Health & Setup

### `GET /api/health`

Returns API status, Lemma connection, email mode, and feature flags.

### `GET /api/health/lemma`

Lemma token and pod reachability details.

### `GET /api/setup`

Setup checklist for demo readiness.

---

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/status` | OAuth enabled flag + login URL |
| GET | `/api/auth/google` | Start Google OAuth flow |
| GET | `/api/auth/google/callback` | OAuth callback (redirect) |
| GET | `/api/auth/me` | Current user profile |
| POST | `/api/auth/logout` | End session |

---

## Uploads

### `POST /api/uploads`

Upload an issue or follow-up photo.

**Query params:**
- `kind` — `petitions` (default) or `follow-up`

**Request:** `multipart/form-data` with `file` field.

**Response:**
```json
{
  "url": "https://res.cloudinary.com/...",
  "storage": "cloudinary"
}
```

**Validation:**
- Max size: `UPLOAD_MAX_BYTES` (default 10 MB)
- Allowed types: JPEG, PNG, WebP, GIF (magic-byte verified)
- Images are optimized before storage

---

## Vision Classification

### `POST /api/vision/classify`

Classify a civic issue from an uploaded photo URL.

**Request:**
```json
{
  "photo_url": "https://...",
  "description": "optional citizen description"
}
```

**Response:**
```json
{
  "classification": {
    "issue_type": "pothole",
    "confidence": 0.87,
    "reasoning": "Visible road crater with broken asphalt",
    "source": "openai_vision"
  },
  "issue_types": ["pothole", "garbage", "streetlight", "..."]
}
```

**Fallback order:** OpenAI Vision → Lemma agent → keyword matching.

**Issue types:** `pothole`, `garbage`, `streetlight`, `water_leak`, `fallen_tree`, `manhole`, `illegal_dumping`, `road_damage`, `other`

---

## Petitions

### `GET /api/petitions`

List petitions. Query: `status`, `mine=true`.

### `GET /api/petitions/pending-approvals`

Draft complaints and pending escalations for the current user.

### `GET /api/petitions/{id}`

Petition detail + activity timeline.

**Extended fields in response:**
- `vision_classification`, `severity_score`, `severity_level`, `severity_explanation`, `infrastructure`, `ai_explanations`

### `POST /api/petitions`

Create and process a new petition.

**Request:**
```json
{
  "photo_url": "https://...",
  "location": { "address": "...", "lat": 12.97, "lng": 77.59 },
  "description": "Large pothole near bus stop",
  "vision_issue_type_override": "pothole",
  "vision_classification": { "issue_type": "pothole", "confidence": 0.9, "reasoning": "...", "source": "openai_vision" }
}
```

**Response:**
```json
{
  "petition": { "id": "...", "status": "draft", "complaint_email_draft": "...", "severity_score": 72 },
  "message": "Petition created — review the drafted email for approval"
}
```

### `POST /api/petitions/check-duplicates`

Check for nearby similar reports before creating a petition.

**Request:**
```json
{
  "lat": 12.97,
  "lng": 77.59,
  "issue_type": "pothole",
  "photo_url": "https://..."
}
```

**Response:**
```json
{
  "has_duplicates": true,
  "duplicates": [
    {
      "petition_id": "...",
      "issue_type": "pothole",
      "distance_m": 120.5,
      "image_similarity": 0.82,
      "likelihood": 0.85,
      "description": "..."
    }
  ]
}
```

### `POST /api/petitions/{id}/approve`

Approve and send complaint or escalation email.

**Request:**
```json
{
  "subject": "...",
  "body": "...",
  "approved": true,
  "is_escalation": false,
  "to_email": "authority@chennaicorporation.gov.in"
}
```

### `POST /api/petitions/{id}/follow-up`

Upload follow-up photo and run resolution verification.

**Request:**
```json
{ "follow_up_photo_url": "https://..." }
```

**Resolution verdict:**
```json
{
  "resolution_verdict": {
    "status": "resolved",
    "resolved": true,
    "confidence": 0.91,
    "reasoning": "Follow-up photo shows pothole has been filled",
    "source": "openai_vision"
  }
}
```

Status values: `resolved`, `partially_resolved`, `not_resolved`

### `DELETE /api/petitions/{id}`

Delete a petition and its activity log.

### `POST /api/petitions/escalation/check`

Find stale petitions and draft escalation emails.

---

## Infrastructure

### `GET /api/infrastructure/nearby`

Fetch map markers for schools, hospitals, bus stops, and stations near a point (cached Overpass).

**Query:** `lat`, `lng`, optional `radius_m`

**Response:**
```json
{
  "markers": [{ "category": "school", "icon": "school", "lat": 12.97, "lng": 77.59, "name": "...", "distance_m": 180 }],
  "source": "cache"
}
```

---

## Analytics

All analytics endpoints are read-only and require no authentication in development.

### `GET /api/analytics/summary`

Full analytics dashboard data.

### `GET /api/analytics/trends?days=30`

Daily complaint counts over the period.

### `GET /api/analytics/severity`

Severity score distribution buckets (0–24, 25–49, 50–74, 75–100).

### `GET /api/analytics/resolution-time`

Average and median resolution time in hours.

### `GET /api/analytics/issue-types?limit=10`

Most common issue types.

### `GET /api/analytics/departments`

Department performance: total complaints, resolved count, resolution rate, avg severity.

### `GET /api/analytics/infrastructure`

Infrastructure-aware analytics.

**Query:** `proximity_m` (default 500), `high_risk_threshold` (default 25)

**Response fields:** `complaints_near_schools`, `complaints_near_hospitals`, `severity_by_school_proximity`, `high_risk_zones`, `avg_severity_near_schools`, `avg_severity_near_hospitals`

`GET /api/analytics/summary` also includes an `infrastructure` object with the same data.

---

## Error responses

```json
{ "detail": "Error message" }
```

| Code | Meaning |
|------|---------|
| 400 | Invalid input |
| 401 | Authentication required |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 502 | Upload/storage failure |

---

## Rate limiting

When `RATE_LIMIT_ENABLED=true` (default), clients are limited to `RATE_LIMIT_REQUESTS_PER_MINUTE` (default 120) requests per IP per minute. Health endpoints are excluded.
