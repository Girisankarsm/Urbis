# CivicLens

**Report civic issues. Route to the right department. Track resolution.**

CivicLens lets citizens photograph potholes, garbage, broken streetlights, and other civic issues, automatically classifies them, drafts formal complaint emails, and tracks resolution over time.

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

Configure SMTP in `.env` for real sends; otherwise emails are logged (demo-safe):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=app-password
DEMO_EMAIL_TO=municipal-demo@example.com
```

## Project structure

```
├── pod/civic-lens/          # Lemma pod bundle (import-ready)
├── backend/                 # FastAPI + Motor (MongoDB)
├── frontend/                # React + Vite + Tailwind
└── docker-compose.yml       # MongoDB 7 + API
```

## Hackathon demo tips

- Seed departments are for **Metro City Municipal Corp** (generic fictional city)
- Single demo user — no auth required
- Escalation threshold: **3 days** (configurable via `ESCALATION_DAYS`)
- Trigger escalation manually: `POST /api/petitions/escalation/check`
