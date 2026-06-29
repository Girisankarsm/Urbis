<p align="center">
  <strong>Urbis</strong><br />
  <em>Report civic issues. Route to the right department. Track resolution.</em>
</p>

<p align="center">
  <a href="https://github.com/Girisankarsm/Urbis">GitHub</a> ·
  <a href="./ARCHITECTURE.md">Architecture</a> ·
  <a href="./API.md">API Reference</a> ·
  <a href="https://gappy.ai">Gappy AI Hackathon</a>
</p>

---

## Overview

**Urbis** is a citizen civic-issue reporting platform. Citizens photograph potholes, garbage, broken streetlights, and similar problems. AI classifies the issue, finds the correct municipal authority, drafts a formal complaint email, and sends it **only after the citizen approves** — from their own Gmail.

Built with **FastAPI · React · MongoDB · Lemma SDK · Google OAuth · Cloudinary**.

| | |
|---|---|
| **Problem** | Citizens don't know which department to contact or how to file a formal complaint |
| **Solution** | Photo + location → AI routing → human-approved email → track resolution |
| **Differentiator** | Human-in-the-loop + citizen-owned Gmail send + nationwide Indian authority routing |

---

## MVP at a glance

| Step | Screen | What happens |
|:----:|--------|--------------|
| 1 | `/` | Welcome onboarding → Google sign-in |
| 2 | `/new` | Upload photo, pin location, add description |
| 3 | Backend | Geocode → classify → route to authority → draft email |
| 4 | `/approvals/:id` | Citizen edits **To**, subject, body → approves |
| 5 | Gmail | Complaint sent from citizen's account to municipal authority |
| 6 | `/dashboard` | Track status, upload follow-up, escalate if unresolved |

```
Welcome (/)  →  Sign in  →  Dashboard (/dashboard)
                                ├─ Report issue (/new)
                                ├─ Approvals (/approvals)
                                └─ Profile (/profile)
```

When Google OAuth is enabled, users only see **their own** petitions and approvals.

---

## Architecture

### System overview

<p align="center">
  <img src="./docs/images/system-architecture.png" alt="Urbis system architecture — React, FastAPI, MongoDB, Lemma, Cloudinary, Gmail" width="900" />
</p>

<p align="center">
  <sub>React SPA → FastAPI backend → MongoDB · Lemma agents · Gmail · Cloudinary · Nominatim · DuckDuckGo</sub>
</p>

| Layer | Stack | Role |
|-------|-------|------|
| **Frontend** | React 18, Vite, Tailwind | Report, approve, track |
| **Backend** | FastAPI, Motor | REST API, OAuth, petition pipeline |
| **Database** | MongoDB | Petitions, users, activity log |
| **AI** | Lemma SDK + OpenAI Vision (optional) | Classify, draft, verify resolution |
| **Email** | Gmail API (primary), Brevo SMTP (fallback) | Citizen-owned complaint delivery |
| **Images** | Cloudinary | Public photo URLs in complaint emails |

### Complaint pipeline

<p align="center">
  <img src="./docs/images/complaint-pipeline.png" alt="Urbis complaint pipeline sequence diagram" width="900" />
</p>

<p align="center">
  <sub>Photo upload → geocode → authority lookup → Lemma classify/draft → human approval → Gmail send → track</sub>
</p>

### Authority routing priority

For locations across India, the backend resolves the government contact in this order:

1. **Regional registry** — verified `.gov.in` contacts for 30+ cities (GCC, BBMP, BMC, TMC, …)
2. **Web search** — DuckDuckGo when the registry has no email
3. **Lemma `issue-classifier`** — WEB_SEARCH + pod knowledge when Lemma is connected
4. **Manual edit** — citizen corrects the **To** field on the approval screen

---

## Features

### Core MVP

| Feature | Description |
|---------|-------------|
| Photo + map reporting | Upload issue photos, pin location with geolocation |
| AI classification | Vision + registry + web search + Lemma agents |
| Human-in-the-loop | Edit recipient, subject, and body before send |
| Gmail send | OAuth — complaints send from the citizen's own Gmail |
| Dashboard & tracking | Filter by status, timeline, follow-up photos |
| Escalation | Auto-draft escalation emails after 3 days without resolution |
| Profile | View account, your reports, delete petitions |

### AI extensions

| Feature | Description |
|---------|-------------|
| Vision classification | Auto-detect issue type from photos with confidence + reasoning |
| Severity analysis | 0–100 score using nearby schools, hospitals, traffic |
| AI explainability | Stored confidence, reasoning, authority routing context |
| Duplicate detection | Warns about nearby similar reports before submission |
| Resolution verification | Before/after image comparison (resolved / partial / not resolved) |
| **Nearby infrastructure analysis** | Overpass POI lookup, distance-decayed severity, map markers |
| Analytics API | Trends, severity distribution, resolution time, department stats |

Weights, alpha, and decay constants live in `backend/app/services/infrastructure/infrastructure_scoring.json` (editable without code changes).

---

## Nearby infrastructure analysis

When a report is submitted, the API queries Openpass (with mirror fallback) for schools, hospitals, clinics, bus stops, stations, government offices, and major roads within a configurable radius. Results are cached in MongoDB (`overpass_cache`, 7-day TTL) keyed by rounded lat/lng.

Severity uses distance-decayed scoring: `finalSeverity = base × (1 + α × normalizedInfra)`. Base issue type always dominates. Overpass failures never block report submission.

Map markers (schools, hospitals, bus stops, stations) appear on the report map via Leaflet marker clustering.

---

## Lemma SDK integration

The FastAPI backend connects to Lemma through **`lemma-sdk`** (`backend/app/services/lemma_service.py`).

| Phase | Lemma resource | Fallback |
|-------|----------------|----------|
| Classify + route | `issue-classifier` agent | Regional registry + geocoding |
| Draft email | `complaint-drafter` agent | Local `draft_complaint_email()` |
| Send email | `send_complaint_email` function | Citizen Gmail → Brevo SMTP |
| Resolution check | `resolution-checker` agent | Heuristic / OpenAI Vision |

**Primary database is MongoDB** — petitions, users, and activity logs. Lemma pod tables are used by agents during classification.

Pod bundle: `pod/civic-lens/` — agents, functions, workflows, municipal knowledge base.

---

## Quick start

**Requirements:** Docker Desktop (or local MongoDB), Python 3.11+, Node 18+

```bash
# One-time setup
./scripts/setup.sh

# Start API + MongoDB
./scripts/start.sh

# Start frontend (second terminal)
cd frontend && npm run dev
```

| Service | URL |
|---------|-----|
| **App** | http://localhost:5173 |
| **API health** | http://localhost:8000/api/health |
| **Lemma health** | http://localhost:8000/api/health/lemma |

**Without Docker** (local MongoDB already running):

```bash
cd backend && MONGODB_URL=mongodb://localhost:27017 .venv/bin/uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

After `.env` changes:

```bash
./scripts/restart-api.sh
```

---

## Environment variables

Copy `.env.example` to `.env`:

| Variable | Purpose |
|----------|---------|
| `MONGODB_URL` | Local Mongo or MongoDB Atlas |
| `LEMMA_REFRESH_TOKEN`, `LEMMA_POD_ID` | Lemma agents (auto-refresh) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth + Gmail send |
| `SMTP_*` | Brevo SMTP fallback |
| `CLOUDINARY_*` | Cloud image storage |
| `OPENAI_API_KEY` | Optional — vision classification + resolution |
| `INFRASTRUCTURE_RADIUS_M` | Overpass search radius for severity (default 500) |
| `SESSION_SECRET` | JWT session signing (required in production) |
| `DEMO_EMAIL_REDIRECT` | Set `false` to send to real authorities |

See `.env.example` for the full list.

---

## Email & auth

**Gmail (recommended):** Citizens sign in with Google; approved complaints send from their Gmail via Gmail API.

1. Enable **Gmail API** in [Google Cloud Console](https://console.cloud.google.com)
2. OAuth redirect URI: `http://localhost:8000/api/auth/google/callback`
3. Add test users if app is in Testing mode

**Brevo SMTP (fallback):** [app.brevo.com](https://app.brevo.com) — free 300 emails/day.

---

## Tests & CI

```bash
./scripts/test.sh          # backend + frontend
cd backend && pytest -q    # API tests
cd frontend && npm test    # Vitest
```

GitHub Actions runs on every push to `main`.

---

## Production deployment

Full guide: **[DEPLOY.md](DEPLOY.md)**

| Component | Platform | Config |
|-----------|----------|--------|
| API | Render (`render.yaml`) | `.env.production.example` |
| Frontend | Vercel | `VITE_API_URL` → Render API URL |
| Database | MongoDB Atlas | `MONGODB_URL` |
| Images | Cloudinary | Required on Render |

```bash
# Pre-flight before deploy
./scripts/check-deploy-ready.sh
```

**Local dev (no Docker):** `./scripts/run-local.sh`  
**Local dev (Docker):** `./scripts/start.sh` then `cd frontend && npm run dev`

---

## Project structure

```
├── docs/images/                 # Architecture diagrams (README)
├── pod/civic-lens/              # Lemma pod bundle
├── backend/app/                 # FastAPI routes, services, models
├── frontend/src/                # React pages and components
├── scripts/                     # setup.sh, start.sh, run-local.sh, check-deploy-ready.sh
├── DEPLOY.md                    # Production hosting guide (Render + Vercel + Atlas)
├── render.yaml                  # Render blueprint
├── docker-compose.yml           # Local: MongoDB + API
├── docker-compose.prod.yml      # Self-hosted API → Atlas
```

---

## Hackathon demo tips

- Start at the **welcome screen** — walk through the 5-step flow before signing in
- Report from a real Indian location — check **authority source** on approval (`registry`, `web_search`, `lemma`)
- Set `DEMO_EMAIL_REDIRECT=false` so emails go to the authority
- Trigger escalation: `POST /api/petitions/escalation/check`
- Analytics: `GET /api/analytics/summary`

---

## License

MIT — Gappy AI Hackathon project.
