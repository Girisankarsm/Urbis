# Urbis

**Report civic issues. Route to the right department. Track resolution.**

Urbis lets citizens photograph potholes, garbage, broken streetlights, and other civic issues. AI classifies each report, drafts a formal complaint email, routes it to the right municipal authority, and tracks resolution over time — with **human approval** before anything is sent.

Built for the [Gappy AI Hackathon](https://gappy.ai) using **Lemma SDK** as the agentic infrastructure layer.

**Repo:** https://github.com/Girisankarsm/Urbis

## Features

| Feature | Description |
|---------|-------------|
| **Welcome onboarding** | Animated intro explains how Urbis works before users enter the app |
| **Photo + map reporting** | Upload issue photos, pin location with geolocation |
| **AI classification** | Lemma agents (or local heuristics) classify issue type and department |
| **Authority routing** | Geocoding + regional contacts (BBMP, BMC, GCC, etc.) |
| **Human-in-the-loop** | Edit and approve complaint emails before send |
| **Gmail send** | OAuth sign-in — complaints send from the citizen's own Gmail |
| **Dashboard & tracking** | Filter petitions by status, timeline, follow-up photos |
| **Escalation** | Auto-draft escalation emails after 3 days without resolution |
| **Cloudinary** | Cloud image storage for production deploys |
| **Tests & CI** | Pytest + Vitest, GitHub Actions on every push |

## User flow

```
Welcome screen (/)  →  Sign in with Google  →  Dashboard (/dashboard)
        │                                              │
        └─ Explains 5-step workflow                    ├─ Report issue
                                                       ├─ Approve emails
                                                       └─ Track petitions
```

1. **Welcome** (`/`) — onboarding explains the full workflow; sign in with Google (or continue in demo mode)
2. **Report Issue** — upload photo, pin location, add description
3. **AI classifies** → drafts complaint email → **Approval screen**
4. **Approve & send** → petition status = `submitted` (from citizen's Gmail when OAuth is on)
5. **Dashboard** — view and filter your petitions by status
6. **Petition Detail** — timeline, upload follow-up photo for resolution check

When Google OAuth is enabled, users only see **their own** petitions, approvals, and profile data.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│  MongoDB (app data) │
│  Vite + Tailwind│     │  images + API    │     │  petitions, logs    │
└─────────────────┘     └────────┬─────────┘     └─────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
            ┌─────────────┐ ┌─────────┐ ┌──────────────┐
            │ Lemma Pod   │ │ Cloudinary│ │ Gmail / Brevo│
            │ agents      │ │ images   │ │ email send   │
            └─────────────┘ └─────────┘ └──────────────┘
```

## Quick start

**Requirements:** Docker Desktop (running), Python 3.11+, Node 18+

```bash
# One-time setup (Python venv, npm, Docker)
./scripts/setup.sh

# Start API + MongoDB (waits for health check)
./scripts/start.sh

# Start frontend (second terminal)
cd frontend && npm run dev
```

| Service | URL |
|---------|-----|
| **App** | http://localhost:5173 |
| **API health** | http://localhost:8000/api/health |

After `.env` changes, reload the API:

```bash
./scripts/restart-api.sh
# or: docker compose up -d --force-recreate api
```

### Manual setup

```bash
cp .env.example .env
python3.11 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-lemma.txt
cd frontend && npm install
docker compose up -d
```

### Demo mode

Without Lemma or SMTP configured, the app still runs locally using built-in heuristics for classification and email drafting. Emails are logged to the console unless SMTP is set up.

Without Google OAuth, the welcome screen offers **Get started** and the app runs in open demo mode (Brevo sender). With OAuth, sign-in is required to report issues and approve emails.

## Environment variables

Copy `.env.example` to `.env` and fill in what you need:

| Variable | Purpose |
|----------|---------|
| `MONGODB_URL` | Local Docker Mongo or [MongoDB Atlas](https://www.mongodb.com/atlas) `mongodb+srv://…` |
| `LEMMA_TOKEN`, `LEMMA_POD_ID` | Connect to Lemma agents |
| `SMTP_*` | Brevo or Gmail SMTP for real email delivery |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth + Gmail send |
| `SESSION_SECRET` | JWT session signing (required in production) |
| `CLOUDINARY_*` | Cloud image storage |
| `FRONTEND_URL` | CORS + OAuth redirect target |
| `ENVIRONMENT` | Set to `production` when deploying |

See `.env.example` for the full list including production cookie settings (`COOKIE_SECURE`, `COOKIE_SAMESITE`).

## Lemma pod

The complete Lemma pod bundle is at `pod/civic-lens/`:

| Resource | Names |
|----------|-------|
| Tables | `petitions`, `departments`, `activity_log` |
| Agents | `issue-classifier`, `complaint-drafter`, `resolution-checker` |
| Functions | `create_petition`, `send_complaint_email`, `escalate_petition`, `update_resolution_status` |
| Workflows | `petition-pipeline`, `escalation-pipeline` |
| Schedule | `daily-resolution-check` (9am daily, 3-day escalation threshold) |

```bash
backend/.venv/bin/lemma auth login
backend/.venv/bin/lemma pods create civic-lens --org <your-org>
backend/.venv/bin/lemma pods import ./pod/civic-lens
lemma records import departments ./pod/civic-lens/seed/departments.json
lemma files upload ./pod/civic-lens/files/knowledge/municipal-departments.md /knowledge/municipal-departments.md
```

Set `LEMMA_TOKEN`, `LEMMA_POD_ID`, and `LEMMA_ORG_ID` in `.env`, then recreate the API container.

## Email (Brevo SMTP)

**Brevo** (recommended — free 300 emails/day): [app.brevo.com](https://app.brevo.com) → SMTP & API → use the SMTP login and verify your sender email.

```
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your-login@smtp-brevo.com
SMTP_PASSWORD=your-smtp-key
SMTP_FROM=your-verified@gmail.com
DEMO_EMAIL_TO=your@gmail.com
```

Complaints are sent **to** the authority email found by geocoding (e.g. BBMP). With Google sign-in, approved emails send **from the citizen's Gmail**. Otherwise Brevo `SMTP_FROM` is used.

## Google sign-in

Citizens sign in with Google; approved complaints send **from their Gmail** via Gmail API (falls back to Brevo if needed).

1. [Google Cloud Console](https://console.cloud.google.com) → create project
2. Enable **Gmail API**
3. **OAuth consent screen** → External → add your Gmail as a **test user** (Testing mode)
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

**Note:** In Testing mode, only approved test users can sign in. For public use, publish the consent screen and complete Google verification for the `gmail.send` scope.

## Image storage (Cloudinary)

Issue photos upload to **Cloudinary** when configured; otherwise they save to local `uploads/` (lost on redeploy).

1. Create a free account at [cloudinary.com](https://cloudinary.com)
2. Add to `.env`:

```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
CLOUDINARY_FOLDER=urbis
```

3. `docker compose build api && docker compose up -d --force-recreate api`
4. Verify: `curl http://localhost:8000/api/health` → `"cloudinary_configured": true`

## Tests & CI

```bash
./scripts/test.sh          # backend (needs MongoDB) + frontend unit tests
cd backend && pytest -q    # API tests only
cd frontend && npm test    # Vitest
```

GitHub Actions runs the same checks on every push to `main` (`.github/workflows/ci.yml`).

## Production deployment

Deploy the API on **Render** and the frontend on **Vercel**.

### API (Render)

1. Connect this repo in [Render](https://render.com)
2. Use `render.yaml` or create a **Web Service** from `backend/Dockerfile`
3. Set environment variables:
   - `ENVIRONMENT=production`
   - `MONGODB_URL` — MongoDB Atlas connection string
   - `SESSION_SECRET` — long random string
   - `FRONTEND_URL` — e.g. `https://urbis.vercel.app`
   - `GOOGLE_REDIRECT_URI` — e.g. `https://urbis-api.onrender.com/api/auth/google/callback`
   - `CORS_ORIGINS` — same as `FRONTEND_URL`
   - `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`
   - Cloudinary, SMTP, Lemma, Google OAuth keys
4. Health check: `GET /api/health`

### Frontend (Vercel)

1. Import repo → **Root Directory:** `frontend`
2. Build: `npm run build` · Output: `dist`
3. Set `VITE_API_URL=https://your-api.onrender.com` (no trailing slash)
4. Redeploy after env changes

### Google OAuth (production)

1. Add production redirect URI in Google Cloud Console
2. **Testing mode:** add testers under OAuth consent screen → Test users
3. **Public launch:** publish consent screen + verify `gmail.send` scope

## Project structure

```
├── pod/civic-lens/              # Lemma pod bundle (import-ready)
├── backend/
│   ├── app/                     # FastAPI routes, services, models
│   └── tests/                   # Pytest (health, auth, petitions)
├── frontend/
│   ├── src/pages/WelcomePage.tsx  # Onboarding + animated loader
│   └── src/pages/DashboardPage.tsx
├── scripts/
│   ├── setup.sh                 # One-time install
│   ├── start.sh                 # Docker up + health wait
│   ├── restart-api.sh           # Reload .env into API container
│   └── test.sh                  # Run all tests
├── render.yaml                  # Render blueprint
├── docker-compose.yml           # MongoDB 7 + API
└── .github/workflows/ci.yml     # CI pipeline
```

## Hackathon demo tips

- Start at the **welcome screen** — walk judges through the 5-step flow before signing in
- Seed departments use **Metro City Municipal Corp** (generic); geocoding routes to real cities (Bengaluru, Mumbai, etc.)
- Escalation threshold: **3 days** (`ESCALATION_DAYS`)
- Trigger escalation manually: `POST /api/petitions/escalation/check`
- Click the **Urbis logo** in the nav anytime to return to the welcome screen

## License

MIT — hackathon project.
