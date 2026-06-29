# Urbis Architecture

Technical architecture for the Urbis civic-issue reporting platform.

## System overview

```
React SPA (Vite)  →  FastAPI REST API  →  MongoDB (primary store)
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   Cloudinary         Lemma SDK          Gmail / SMTP
   (images)           (agents)           (email send)
        │                  │
        ▼                  ▼
   Image optimize     OpenAI Vision (optional)
   + validation       Overpass POI lookup
```

## Core principles

1. **Human-in-the-loop** — no email is sent without citizen approval
2. **Extension over replacement** — new AI features are optional modules; existing flows unchanged
3. **MongoDB as source of truth** — petitions, users, activity; Lemma pod tables are secondary
4. **Graceful fallbacks** — OpenAI → Lemma → keyword/heuristic at every AI layer

## Backend modules

| Module | Path | Purpose |
|--------|------|---------|
| Petition pipeline | `services/petitions.py` | Create, approve, follow-up, escalation |
| Vision classification | `services/vision_classification.py` | Photo → issue type + confidence |
| Severity analysis | `services/severity_analysis.py` | 0–100 score with POI factors |
| Explainability | `services/explainability.py` | Store AI reasoning on petitions |
| Duplicate detection | `services/duplicate_detection.py` | Nearby + image-similar reports |
| Resolution verification | `services/resolution_verification.py` | Before/after image comparison |
| Analytics | `services/analytics.py` | Aggregation queries |
| Security | `services/security.py` | Upload validation, magic bytes |
| Image optimization | `services/image_optimization.py` | Resize/compress before storage |
| **Infrastructure** | `services/infrastructure/` | Overpass fetch, cache, distance, map markers |
| **Infra severity** | `services/severity/infra_severity.py` | Distance-decayed scoring formula |
| Lemma integration | `services/lemma_service.py` | Agents, functions, token refresh |
| Authority routing | `authority_lookup.py`, `authority_discovery.py` | Registry + web search |

## Petition creation pipeline

```
POST /api/petitions
  1. Reverse geocode (Nominatim)
  2. Vision classify photo (optional)
  3. Authority routing (registry → web search → Lemma)
  4. Draft complaint email
  5. Infrastructure analysis (cached Overpass → distance-decayed severity)
  6. Build AI explanations + severity_explanation
  7. Save to MongoDB (status: draft)
```

## Infrastructure analysis

| Component | Path | Role |
|-----------|------|------|
| Overpass fetch | `infrastructure/overpass_service.py` | Combined query, 8s timeout, mirror fallback |
| Cache | `infrastructure/cache.py` | Mongo `overpass_cache`, TTL 7 days, key `overpass:lat:lng:radius` |
| Distance | `infrastructure/distance_utils.py` | Haversine, classify, nearest-per-category |
| Scoring | `severity/infra_severity.py` | `weight × exp(-distance/decay)` formula |
| Config | `infrastructure/infrastructure_scoring.json` | radius, alpha, weights (hot-editable) |

On Overpass failure: `{ data: null, source: 'unavailable' }` — report continues with base severity only.

---

## Petition creation pipeline (legacy detail)

```
POST /api/petitions
  1. Reverse geocode (Nominatim)
  2. Vision classify photo (optional, if VISION_ENABLED)
  3. Authority routing (registry → web search → Lemma)
  4. Draft complaint email (local + Lemma drafter)
  5. Severity analysis (Overpass POI lookup)
  6. Build AI explanations
  7. Save to MongoDB (status: draft)
```

## MongoDB petition fields (extended)

| Field | Type | Description |
|-------|------|-------------|
| `vision_classification` | object | `{issue_type, confidence, reasoning, source, user_override}` |
| `severity_score` | int | 0–100 |
| `severity_level` | string | `low`, `moderate`, `high`, `critical` |
| `severity_factors` | object | POI boosts and factor breakdown |
| `ai_explanations` | object | Vision, authority, severity explanations |
| `infrastructure` | object | Distances, infra_score, contributions, source |
| `severity_explanation` | string | Traceable severity reason from contributions |
| `resolution_verdict` | object | `{status, resolved, confidence, reasoning, source}` |

## Follow-up resolution pipeline

```
POST /api/petitions/:id/follow-up
  1. Store follow-up photo URL
  2. verify_resolution() — OpenAI vision → Lemma resolution-checker → heuristic
  3. Update status (resolved / under_review)
  4. Log resolution_checked event
```

## Duplicate detection

Before petition creation, the frontend calls `POST /api/petitions/check-duplicates`:

- Bounding-box query on `location.lat` / `location.lng`
- Haversine distance filter (default 500m)
- Issue type match + perceptual image hash similarity
- Returns likelihood score; user can continue anyway

## Analytics

Read-only endpoints under `/api/analytics/`:

- `GET /summary` — full dashboard data
- `GET /trends` — daily complaint counts
- `GET /severity` — severity bucket distribution
- `GET /resolution-time` — avg/median hours to resolve
- `GET /issue-types` — most common issue types
- `GET /departments` — department performance stats

## Security

| Control | Implementation |
|---------|----------------|
| Upload validation | Magic-byte check, allowed MIME types, size limit |
| Filename sanitization | Strip path traversal characters |
| Rate limiting | In-memory middleware (120 req/min per IP) |
| Input validation | Pydantic models on all request bodies |
| OAuth scoping | User-scoped petitions when Google auth enabled |

## Performance

- MongoDB indexes on `created_at`, `status`, `location`, `issue_type`, `severity_score`
- Image optimization (max 1920px, JPEG quality 85) before upload
- Lazy loading on petition detail images (frontend)
- Bounding-box geo queries instead of full collection scans

## Lemma pod (`pod/civic-lens/`)

| Resource | Name |
|----------|------|
| Agents | `issue-classifier`, `complaint-drafter`, `resolution-checker` |
| Functions | `send_complaint_email`, `create_petition`, `escalate_petition` |
| Workflows | `petition-pipeline`, `escalation-pipeline` |

FastAPI invokes Lemma agents via `lemma-sdk`; MongoDB remains the primary data store.

## Environment variables (AI features)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Enables OpenAI vision for classification + resolution |
| `VISION_ENABLED` | Toggle vision classification (default: true) |
| `VISION_MODEL` | OpenAI model (default: `gpt-4o-mini`) |
| `DUPLICATE_RADIUS_M` | Duplicate search radius in meters |
| `SEVERITY_POI_RADIUS_M` | POI lookup radius for severity |
| `RATE_LIMIT_ENABLED` | Toggle API rate limiting |
| `LEMMA_REFRESH_TOKEN` | Auto-refresh Lemma access tokens |

## Deployment

See **[DEPLOY.md](DEPLOY.md)** for the full production guide.

| Environment | API | Frontend | Database |
|-------------|-----|----------|----------|
| Local | `uvicorn` or Docker Compose | Vite `:5173` | Local MongoDB |
| Production | Render (`render.yaml`) | Vercel (`VITE_API_URL`) | MongoDB Atlas |

Health endpoints:

- `GET /api/health/live` — liveness (load balancers)
- `GET /api/health` — full status including Lemma, Cloudinary, email mode
- **Database:** MongoDB Atlas
- **Images:** Cloudinary
