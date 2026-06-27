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
| **AI classification** | Web search + Lemma agents + regional registry for issue type and department |
| **Authority routing** | Geocoding + live web discovery + 30+ Indian cities (BBMP, BMC, GCC, TMC, etc.) |
| **Human-in-the-loop** | Edit recipient, subject, and body before send |
| **Gmail send** | OAuth sign-in — complaints send from the citizen's own Gmail |
| **Profile** | View account, your reports, delete petitions |
| **Dashboard & tracking** | Filter petitions by status, timeline, follow-up photos |
| **Escalation** | Auto-draft escalation emails after 3 days without resolution |
| **AI vision classification** | Auto-detect issue type from photos with confidence + reasoning |
| **Severity analysis** | 0–100 score using nearby schools, hospitals, traffic, and issue type |
| **AI explainability** | Stored confidence, reasoning, and authority routing explanations |
| **Duplicate detection** | Warns about nearby similar reports before submission |
| **Resolution verification** | Before/after image comparison (resolved / partial / not resolved) |
| **Analytics API** | Complaint trends, severity distribution, resolution time, department stats |
| **Cloudinary** | Cloud image storage for production deploys |
| **Tests & CI** | Pytest + Vitest, GitHub Actions on every push |

## User flow

End-to-end journey from reporting an issue to sending a complaint to the municipal authority:

```
Welcome (/)  →  Sign in (Google)  →  Dashboard (/dashboard)
       │                                    │
       └─ 5-step onboarding                 ├─ Report issue (/new)
                                            ├─ Approvals (/approvals)
                                            └─ Profile (/profile)
```

### Step-by-step

| Step | Where | What happens |
|------|--------|----------------|
| **1. Welcome** | `/` | Animated onboarding explains the workflow. Sign in with Google (required when OAuth is on). |
| **2. Report issue** | `/new` | Citizen uploads a photo, pins location on the map (or uses GPS), and adds a short description. |
| **3. AI classifies & routes** | Backend | Geocoding reads city/state → web search finds the official municipal email → Lemma agent enriches if needed → complaint email is drafted. |
| **4. Human approval** | `/approvals/:id` | Citizen reviews and edits the **To** address, subject, and body. Nothing is sent without explicit approval. |
| **5. Email sent** | Gmail / Brevo | Complaint goes to the authority (e.g. GCC, TMC, BBMP) from the citizen's Gmail when OAuth is on. |
| **6. Track** | `/dashboard`, `/petitions/:id` | Status timeline, follow-up photos, escalation after 3 days if unresolved. |
| **7. Profile** | `/profile` | View your reports and delete petitions you no longer want listed. |

When Google OAuth is enabled, users only see **their own** petitions, approvals, and profile data.

### Authority routing priority

For any location in India (and beyond), the backend resolves the government contact in this order:

1. **Regional registry** — verified `.gov.in` contacts for 30+ Indian cities  
2. **Web search** — DuckDuckGo when the registry has no email  
3. **Lemma `issue-classifier` agent** — WEB_SEARCH + pod knowledge when Lemma is connected  
4. **Manual edit** — citizen corrects the **To** field on the approval screen  

See [ARCHITECTURE.md](./ARCHITECTURE.md) and [API.md](./API.md) for full technical documentation.

## Architecture

### System overview

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌─────────────────────┐
│   React Frontend    │────▶│    FastAPI Backend       │────▶│  MongoDB            │
│   Vite + Tailwind   │     │    REST API + auth       │     │  petitions, users,  │
│   localhost:5173    │     │    localhost:8000        │     │  activity_log       │
└─────────────────────┘     └────────────┬─────────────┘     └─────────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
    ┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
    │  Cloudinary      │        │  Lemma SDK       │        │  Email delivery  │
    │  public images   │        │  (lemma-sdk)     │        │  Gmail OAuth →   │
    │                  │        │                  │        │  Brevo SMTP      │
    └──────────────────┘        └────────┬─────────┘        └──────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  Lemma Pod (cloud)   │
                              │  pod/civic-lens/     │
                              │  agents + functions  │
                              └──────────────────────┘
```

### Lemma SDK layer

The FastAPI backend connects to Lemma through **`lemma-sdk`** (`backend/app/services/lemma_service.py`). Lemma is the **agentic infrastructure** — AI agents with tools run on Lemma's cloud; your app calls them over the API.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI (Urbis API)                             │
│  petitions.py  →  lemma_service.py  →  from lemma_sdk import Pod        │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                    LEMMA_TOKEN + LEMMA_POD_ID + LEMMA_ORG_ID
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Lemma Pod: civic-lens (cloud)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  AGENTS (pod.agents.run)                                                │
│    • issue-classifier   — WEB_SEARCH + POD tools → issue type + email   │
│    • complaint-drafter  — reads petition → formal complaint email       │
│    • resolution-checker — compare follow-up photo vs original           │
├─────────────────────────────────────────────────────────────────────────┤
│  FUNCTIONS (pod.functions.run)                                          │
│    • send_complaint_email  — SMTP send on Lemma runtime                 │
│    • create_petition, escalate_petition, update_resolution_status       │
├─────────────────────────────────────────────────────────────────────────┤
│  DATA & KNOWLEDGE                                                       │
│    • Tables: petitions, departments, activity_log (on Lemma)            │
│    • /knowledge/municipal-departments.md — routing reference for agents │
│    • Workflows: petition-pipeline, escalation-pipeline                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**When Lemma runs in the petition pipeline:**

| Phase | Lemma usage | Fallback if Lemma unavailable / times out |
|-------|-------------|-------------------------------------------|
| **Classify + route** | `issue-classifier` agent (after local web search) | Regional registry + geocoding |
| **Draft email** | `complaint-drafter` agent | Local Python `draft_complaint_email()` |
| **Send email** | `send_complaint_email` function | Citizen Gmail → Brevo SMTP |

**Primary app database is MongoDB** — petitions, users, and activity logs live there. Lemma pod tables are used by agents during classification; the React app always reads/writes through the FastAPI + MongoDB path.

### Complaint pipeline (data flow)

```
Photo upload → Geocode (Nominatim)
      → Web authority discovery (DuckDuckGo)
      → [optional] Lemma issue-classifier
      → Draft email (local + optional Lemma drafter)
      → Status: draft → Approval UI
      → Citizen approves → Gmail / Lemma function / Brevo
      → Status: submitted → Dashboard timeline
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
| `DEMO_EMAIL_REDIRECT` | Set `false` to send to real authorities (not your inbox) |
| `AUTHORITY_DISCOVERY_ENABLED` | Web search for municipal emails (default `true`) |
| `API_BASE_URL` | Public API URL for local upload links (e.g. `http://localhost:8000`) |
| `FRONTEND_URL` | CORS + OAuth redirect target |
| `ENVIRONMENT` | Set to `production` when deploying |

See `.env.example` for the full list including production cookie settings (`COOKIE_SECURE`, `COOKIE_SAMESITE`).

## Lemma SDK integration

### Python client (`lemma-sdk`)

The backend uses the official SDK to talk to your deployed pod:

```python
from lemma_sdk import Pod

pod = Pod(pod_id=settings.lemma_pod_id, token=settings.lemma_token, org_id=settings.lemma_org_id)
pod.agents.run("issue-classifier", prompt)      # classify + find authority
pod.agents.run("complaint-drafter", prompt)     # draft formal email
pod.functions.run("send_complaint_email", data) # send via SMTP on Lemma
```

All calls are wrapped in `backend/app/services/lemma_service.py` and invoked from `backend/app/services/petitions.py`.

### Pod bundle (`pod/civic-lens/`)

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

Issue photos upload to **Cloudinary** when configured (public URLs in complaint emails). In development, if Cloudinary fails, the app falls back to local `uploads/` at `API_BASE_URL`.

**Cloudinary API key needs Upload (create) permission** — Admin is not required. Create a scoped key with upload enabled in the [Cloudinary dashboard](https://console.cloudinary.com).

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
- Report from a real Indian location (e.g. Trivandrum, Bengaluru) — check **Contact source** on approval (`web_search`, `lemma`, or `registry`)
- Set `DEMO_EMAIL_REDIRECT=false` so emails go to the authority, not your inbox
- Escalation threshold: **3 days** (`ESCALATION_DAYS`)
- Trigger escalation manually: `POST /api/petitions/escalation/check`
- Click the **Urbis logo** in the nav anytime to return to the welcome screen

## License

MIT — hackathon project.
