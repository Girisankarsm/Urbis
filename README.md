# Urbis

**Report civic issues. Route to the right department. Track resolution.**

Urbis lets citizens photograph potholes, garbage, broken streetlights, and other civic issues, automatically classifies them, drafts formal complaint emails, and tracks resolution over time.

Built for the [Gappy AI Hackathon](https://gappy.ai) using **Lemma SDK** as the agentic infrastructure layer.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│  MongoDB (app data) │
│  Vite + Tailwind│     │  images + API    │     │  petitions, logs    │
└─────────────────┘     └────────┬─────────┘     └─────────────────────┘
                                 │
                                 ▼ (when deployed)
                        ┌─────────────────────┐
                        │  Lemma Pod          │
                        │  agents · workflows │
                        │  functions · tables │
                        └─────────────────────┘
```

## Quick start (demo mode)

Demo mode runs the full core loop locally without Lemma cloud — AI classification and email drafting use built-in heuristics; emails log to console unless SMTP is configured.

```bash
# One-time setup (Python 3.11 venv, npm, Docker)
./scripts/setup.sh

# Start frontend (in a second terminal)
cd frontend && npm run dev
```

Open http://localhost:5173 · API health: http://localhost:8000/api/health

**Requirements:** Docker Desktop (running), Python 3.11+, Node 18+

### Manual setup

```bash
cp .env.example .env
python3.11 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-lemma.txt
cd frontend && npm install
docker compose up -d
```

### Demo flow

1. **Report Issue** — upload photo, pin location (with geolocation), add description
2. AI classifies issue → drafts complaint email → **Approval screen**
3. Approve & send → petition status = `submitted`
4. **Dashboard** — filter by status
5. **Petition Detail** — timeline, upload follow-up photo for resolution check

## Lemma pod (import when ready)

The complete Lemma pod bundle is at `pod/civic-lens/`:

| Resource | Names |
|----------|-------|
| Tables | `petitions`, `departments`, `activity_log` |
| Agents | `issue-classifier`, `complaint-drafter`, `resolution-checker` |
| Functions | `create_petition`, `send_complaint_email`, `escalate_petition`, `update_resolution_status` |
| Workflows | `petition-pipeline`, `escalation-pipeline` |
| Schedule | `daily-resolution-check` (9am daily, 3-day escalation threshold) |

```bash
# Lemma CLI is in backend/.venv after setup
backend/.venv/bin/lemma auth login
backend/.venv/bin/lemma pods create civic-lens --org <your-org>
backend/.venv/bin/lemma pods import ./pod/civic-lens
lemma records import departments ./pod/civic-lens/seed/departments.json
lemma files upload ./pod/civic-lens/files/knowledge/municipal-departments.md /knowledge/municipal-departments.md
```

Or install globally: `brew install python@3.11 && pip3.11 install lemma-terminal==0.5.0`

Set `LEMMA_TOKEN` and `LEMMA_POD_ID` in `.env` to connect the FastAPI backend to Lemma.

## Email (optional)

Configure SMTP in `.env` for real sends to municipal authorities; otherwise emails are logged (demo-safe).

**Brevo** (recommended — free 300 emails/day): [app.brevo.com](https://app.brevo.com) → SMTP & API → use the SMTP login (e.g. `xxx@smtp-brevo.com`) and verify your sender email.

```
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your-login@smtp-brevo.com
SMTP_PASSWORD=your-smtp-key
SMTP_FROM=your-verified@gmail.com
DEMO_EMAIL_TO=your@gmail.com
```

After editing `.env`, reload env into Docker:

```bash
docker compose up -d --force-recreate api
```

Complaints are sent **to** the authority email found by geocoding (e.g. BBMP). With Google sign-in (below), approved emails send **from the citizen's Gmail**. Otherwise Brevo `SMTP_FROM` is used.

## Google sign-in (optional)

Citizens sign in with Google; approved complaints send **from their Gmail** via Gmail API (falls back to Brevo if needed).

1. [Google Cloud Console](https://console.cloud.google.com) → create project
2. Enable **Gmail API**
3. **OAuth consent screen** → External → add your Gmail as a **test user**
4. **Credentials** → OAuth 2.0 Client ID → Web application
5. Authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
6. Add to `.env`:

```
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173
SESSION_SECRET=long-random-string
```

7. `docker compose up -d --force-recreate api`

Without Google OAuth, the app runs in open demo mode (Brevo sender). With OAuth, report & approve require sign-in.

## Image storage (Cloudinary)

Issue photos and follow-up images upload to **Cloudinary** when configured; otherwise they save to local `uploads/` (lost on redeploy).

1. Create a free account at [cloudinary.com](https://cloudinary.com)
2. Copy **Cloud name**, **API Key**, **API Secret** from the dashboard
3. Add to `.env`:

```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
CLOUDINARY_FOLDER=urbis
```

4. `docker compose build api && docker compose up -d --force-recreate api`
5. Verify: `curl http://localhost:8000/api/health` → `"cloudinary_configured": true`

## Project structure

```
├── pod/civic-lens/          # Lemma pod bundle (import-ready)
├── backend/                 # FastAPI + Motor (MongoDB)
├── frontend/                # React + Vite + Tailwind
└── docker-compose.yml       # MongoDB 7 + API
```

## Hackathon demo tips

- Seed departments are for **Metro City Municipal Corp** (generic fictional city)
- Optional **Google sign-in** — complaints send from the citizen's Gmail when configured
- Escalation threshold: **3 days** (configurable via `ESCALATION_DAYS`)
- Trigger escalation manually: `POST /api/petitions/escalation/check`

## Production deployment

Deploy the API on **Render** and the frontend on **Vercel** (or any static host).

### 1. API (Render)

1. Push this repo to GitHub and connect it in [Render](https://render.com)
2. Use the included `render.yaml` blueprint or create a **Web Service** from `backend/Dockerfile`
3. Set environment variables (see `.env.example`):
   - `ENVIRONMENT=production`
   - `MONGODB_URL` — MongoDB Atlas connection string
   - `SESSION_SECRET` — long random string (Render can auto-generate)
   - `FRONTEND_URL` — e.g. `https://urbis.vercel.app`
   - `GOOGLE_REDIRECT_URI` — e.g. `https://urbis-api.onrender.com/api/auth/google/callback`
   - `CORS_ORIGINS` — same as `FRONTEND_URL`
   - `COOKIE_SECURE=true` and `COOKIE_SAMESITE=none` (required for cross-origin cookies)
   - Cloudinary, SMTP, Lemma keys as needed
4. Health check: `GET /api/health`

### 2. Frontend (Vercel)

1. Import the repo; set **Root Directory** to `frontend`
2. Build command: `npm run build` · Output: `dist`
3. Environment variable: `VITE_API_URL=https://your-api.onrender.com` (no trailing slash)
4. Redeploy after changing `VITE_API_URL`

### 3. Google OAuth (production)

1. Google Cloud Console → OAuth client → add authorized redirect URI for your Render API callback
2. **Testing mode**: add each tester under OAuth consent screen → Test users
3. **Public launch**: publish the consent screen and complete Google verification for `gmail.send`

### 4. Tests & CI

```bash
./scripts/test.sh          # backend (needs MongoDB) + frontend unit tests
cd backend && pytest -q    # API tests only
cd frontend && npm test    # Vitest
```

GitHub Actions runs the same checks on every push to `main` (`.github/workflows/ci.yml`).
