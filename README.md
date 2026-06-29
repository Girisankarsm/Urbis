<p align="center">
  <strong style="font-size: 1.5rem;">Urbis</strong><br />
  <em>Citizen civic-issue reporting — photo, route, approve, send from your Gmail.</em>
</p>

<p align="center">
  <a href="https://gappy.ai">Gappy AI Hackathon</a> ·
  <a href="https://lemma.work">Lemma SDK</a> ·
  <a href="https://github.com/Girisankarsm/Urbis">GitHub</a>
</p>

<p align="center">
  <a href="https://urbis-lemma.vercel.app">Live app</a> ·
  <a href="https://urbis-ce0h.onrender.com/api/health/live">API health</a> ·
  <a href="./docs/ARCHITECTURE.md">Architecture</a> ·
  <a href="./docs/API.md">API</a> ·
  <a href="./docs/DEPLOY.md">Deploy</a>
</p>

---

## Table of contents

- [Live demo](#live-demo)
- [The problem](#the-problem)
- [What Urbis does](#what-urbis-does)
- [How it works](#how-it-works)
- [Features](#features)
- [Lemma SDK integration](#lemma-sdk-integration)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Environment variables](#environment-variables)
- [Tests & CI](#tests--ci)
- [Production deployment](#production-deployment)
- [Project structure](#project-structure)
- [Hackathon demo script](#hackathon-demo-script)
- [Documentation](#documentation)
- [License](#license)

---

## Live demo

| | URL |
|---|-----|
| **App (Vercel)** | https://urbis-lemma.vercel.app |
| **API (Render)** | https://urbis-ce0h.onrender.com |
| **Health check** | https://urbis-ce0h.onrender.com/api/health/live |
| **Lemma status** | https://urbis-ce0h.onrender.com/api/health/lemma |

Sign in with Google to report issues, approve AI-drafted emails, and track petitions on the dashboard.

---

## The problem

Citizens notice potholes, garbage, broken streetlights, and drainage issues every day — but most never get reported. The barrier is friction: wrong department, formal email writing, and no follow-up.

**Urbis** removes that friction: **photo + location → AI classifies and routes → you approve → email sends from your Gmail → status tracked end-to-end.**

---

## What Urbis does

| Audience | Value |
|----------|--------|
| **Citizens** | Report in under a minute. Nothing is sent without your approval. |
| **Municipalities** | Structured, location-tagged complaints routed to the correct desk. |
| **Community** | Hub to discover and upvote issues that need urgent attention. |
| **Hackathon judges** | Lemma-first agentic pipeline with verified-registry fallback and full audit trail. |

---

## How it works

```
Report photo + pin  →  Lemma classifies & routes  →  Draft complaint email
        →  You review & approve  →  Sent from your Gmail  →  Track on Dashboard
        →  Community upvotes on Hub  →  Follow-up photo checks resolution
```

| Step | Route | What happens |
|:----:|-------|--------------|
| 1 | `/` | Welcome → Google sign-in |
| 2 | `/new` | Upload photo, pin location, describe issue |
| 3 | Backend | Geocode → **Lemma pod** (workflow + agents) → draft email |
| 4 | `/approvals/:id` | Edit recipient, subject, body → approve |
| 5 | Gmail | Complaint sent from the citizen's account |
| 6 | `/dashboard` | Track status, approve drafts, upload follow-up |
| 7 | `/hub` | Browse public reports, upvote issues that matter |

---

## Features

### Core

- Photo + map reporting with geolocation and duplicate warnings
- Lemma-first routing to the right municipal department
- Human-in-the-loop — edit To, subject, and body before send
- Gmail delivery from the citizen's own account
- Dashboard with status filters, timeline, and follow-up photos
- Community Hub with public reports and upvotes
- Auto-escalation after configurable days without resolution

### AI & infrastructure

- Optional OpenAI Vision classification
- Severity scoring with nearby infrastructure (schools, hospitals, transit)
- Resolution verification (before/after photos)
- Analytics API — trends, departments, resolution times
- Verified `.gov.in` authority registry with source links

---

## Lemma SDK integration

Urbis uses the **[Lemma SDK](https://github.com/lemma-work/lemma-platform)** as its primary agentic layer. When the pod is reachable, **Lemma runs first** on every report. Local verified contacts are fallback only.

### civic-lens pod (`pod/civic-lens/`)

| Type | Resources |
|------|-----------|
| **Agents** | `issue-classifier` · `complaint-drafter` · `resolution-checker` |
| **Functions** | `create_petition` · `send_complaint_email` · `escalate_petition` · `update_resolution_status` |
| **Workflows** | `petition-pipeline` · `escalation-pipeline` |
| **Tables** | `petitions` · `departments` · `activity_log` |
| **Schedule** | `daily-resolution-check` → escalation workflow |

### When each fires

| User action | Lemma resources |
|-------------|-----------------|
| Submit report | `petition-pipeline` → `create_petition` → `issue-classifier` → `complaint-drafter` |
| Approve & send | `send_complaint_email` (+ Gmail from citizen) |
| Upload follow-up | `resolution-checker` → `update_resolution_status` |
| Escalate stale case | `escalation-pipeline` → `escalate_petition` |

Each petition stores `processing_path` (`lemma` | `fallback`) and `lemma_invocations[]` for audit.

---

## Architecture

<p align="center">
  <img src="./docs/images/system-architecture.png" alt="Urbis system architecture" width="880" />
</p>

<p align="center">
  <img src="./docs/images/complaint-pipeline.png" alt="Complaint pipeline" width="880" />
</p>

<p align="center">
  <sub>React → FastAPI → MongoDB · Lemma pod · Gmail · Cloudinary · Nominatim</sub>
</p>

Full technical write-up: **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)**

---

## Tech stack

| Layer | Technology | Role |
|-------|------------|------|
| Frontend | React 18, Vite, Tailwind | Report, approve, hub, dashboard |
| API | FastAPI, Motor | OAuth, petition pipeline, hub |
| Database | MongoDB Atlas | Petitions, users, activity, upvotes |
| AI | Lemma SDK (+ optional OpenAI Vision) | Classify, draft, verify resolution |
| Auth | Google OAuth | Sign-in + Gmail send |
| Email | Gmail API (primary), Brevo SMTP (fallback) | Citizen-owned delivery |
| Images | Cloudinary | Persistent photo URLs |
| Hosting | Vercel (frontend) + Render (API) | Production |

---

## Quick start

**Requirements:** Docker (or local MongoDB), Python 3.11+, Node 18+

```bash
git clone https://github.com/Girisankarsm/Urbis.git
cd Urbis
./scripts/setup.sh          # installs deps, copies .env
./scripts/run-local.sh      # API + frontend together
```

| Service | URL |
|---------|-----|
| App | http://localhost:5173 |
| API health | http://localhost:8000/api/health |
| Lemma health | http://localhost:8000/api/health/lemma |

### Lemma setup (full demo)

```bash
cd backend && .venv/bin/lemma auth login
cd .. && ./scripts/sync-lemma-env.sh
# Set LEMMA_POD_ID and LEMMA_ORG_ID from lemma.work dashboard
./scripts/restart-api.sh
```

Confirm `/api/health/lemma` returns `live: true` before demoing.

### Without Docker

```bash
# Terminal 1 — API
cd backend && MONGODB_URL=mongodb://localhost:27017 .venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

---

## Environment variables

Copy `.env.example` → `.env`.

| Variable | Purpose |
|----------|---------|
| `MONGODB_URL` | Local MongoDB or Atlas connection string |
| `LEMMA_REFRESH_TOKEN`, `LEMMA_POD_ID`, `LEMMA_ORG_ID` | Lemma civic-lens pod |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Sign-in + Gmail send |
| `CLOUDINARY_*` | Image hosting (required on Render) |
| `SMTP_*` | Brevo fallback if Gmail unavailable |
| `OPENAI_API_KEY` | Optional vision + resolution |
| `DEMO_EMAIL_REDIRECT` | Set `false` to email real authorities |

Templates: `.env.example` (local) · `.env.production.example` (Render/Vercel)

---

## Tests & CI

```bash
./scripts/test.sh              # backend + frontend
cd backend && pytest -q
cd frontend && npm test
```

GitHub Actions runs on every push to `main`.

---

## Production deployment

See **[docs/DEPLOY.md](docs/DEPLOY.md)** for Render + Vercel + MongoDB Atlas + Google OAuth + Cloudinary.

```bash
./scripts/check-deploy-ready.sh
```

| Component | Platform |
|-----------|----------|
| API | Render (`render.yaml`) |
| Frontend | Vercel (`frontend/vercel.json` proxies `/api` to Render) |
| Database | MongoDB Atlas |
| Lemma pod | lemma.work |

---

## Project structure

```
Urbis/
├── backend/                 FastAPI API, services, tests
├── frontend/                React + Vite SPA
├── pod/civic-lens/          Lemma agents, functions, workflows
├── docs/                    Architecture, API reference, deploy guide
├── scripts/                 setup, run-local, sync-lemma-env, deploy checks
├── docker-compose.yml       Local MongoDB + API
├── render.yaml              Render production blueprint
├── .env.example             Local environment template
└── .env.production.example  Production environment template
```

---

## Hackathon demo script

**~90 seconds**

1. Open https://urbis-lemma.vercel.app → sign in with Google.
2. Check https://urbis-ce0h.onrender.com/api/health/lemma → `live: true`.
3. **Report** a civic issue (photo + pin in Chennai/Bengaluru).
4. **Dashboard** → open draft → **Review & Approve** → verify authority email.
5. **Send** from Gmail → timeline shows `Sent`.
6. **Hub** → upvote the public report.
7. Show petition record: `processing_path: lemma`.

**Submission:** [GitHub](https://github.com/Girisankarsm/Urbis) · Lemma pod: `pod/civic-lens/`

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, pipelines, modules |
| [docs/API.md](./docs/API.md) | REST API reference |
| [docs/DEPLOY.md](./docs/DEPLOY.md) | Production hosting guide |
| [pod/civic-lens/README.md](./pod/civic-lens/README.md) | Lemma pod resources |

---

## License

MIT — built for the [Gappy AI Hackathon](https://gappy.ai).
