# Facility Assessment Report Generator

A submission for the **Medelite Technical Case Study: Facility Assessment Report Generator**.

Enter a CMS Certification Number (CCN) → pull the facility's public data live
from the CMS Provider Data Catalog API → layer on manual operational inputs →
download a branded, print-ready **Facility Assessment Snapshot** as PDF or
Word. Built end-to-end — backend API, frontend UI, data pipeline, PDF/docx
rendering, tests, Docker, and CI — in **under 1 hour**, using
[Claude Code](https://claude.com/claude-code) as a hands-on engineering
partner.

> **Live demo:** [medelite-frontend.onrender.com](https://medelite-frontend.onrender.com)
> **Test CCN:** `686123` (Kendall Lakes Healthcare and Rehab Center, FL)
>
> Note: hosted on Render's free tier — the first request after a period of
> inactivity may take 30–60 seconds while the service wakes up.

---

## What this is

A lightweight "micro-app" that replaces the manual workflow of digging
through CMS public databases and internal notes before a facility outreach
or partnership decision. One CCN in, one polished report out.

It implements:

- ✅ **The full required MVP** — dynamic CCN lookup, live CMS API data engine,
  facility-name override, manual operational inputs, one-click PDF export,
  and a dynamic Medicare Care Compare hyperlink in the exported document.
- ✅ **All optional bonus features** — the full 12-line hospitalization/ED
  metrics table (short-stay + long-stay, each with facility/national/state
  values), `.docx` export, Chart.js visualizations, and structured error
  handling for invalid/missing CCNs.
- ✅ **The hard branding guardrail** — the "INFINITE — Managed by MEDELITE"
  header is a static brand asset on every page and every export and is
  enforced never to be overwritten by the facility name, with automated
  tests on both services proving it.

### Beyond the brief

Two features that weren't asked for, added to show what "production-minded"
looks like beyond satisfying a checklist:

- **AI-generated narrative insights** — an OpenAI-backed summary of each
  facility's performance is generated automatically and included in the
  report, with a deterministic rule-based fallback if no API key is
  configured, so the feature never hard-fails.
- **Saved lookup history + side-by-side comparison** — every lookup is
  persisted (SQLite via Django's ORM) so a user can revisit a past report
  without re-querying CMS, and compare two or more facilities side by side.
  On top of that comparison view sits **Sanavox**, a small embedded AI
  assistant (rate-limited to a few questions per session) that answers
  follow-up questions about the facilities being compared, grounded only in
  their actual CMS + manual data.

Plus the smaller things that don't show up in a feature list but affect
whether a real user could pick this up cold: contextual hover-tooltips on
every manual input field (so a new-joiner knows what to type), a consistent
design system carrying Medelite's brand gradient across the whole UI, and a
responsive layout with a properly pinned footer.

---

## Architecture

Two decoupled, independently runnable Python services — a deliberate choice
to keep the data/processing layer and the UI layer swappable rather than
locking them together in one framework:

```
┌──────────────────┐        HTTP        ┌──────────────────────┐        ┌─────────────────────┐
│  Django frontend  │ ─────────────────▶ │   FastAPI backend     │ ─────▶ │ CMS Provider Data    │
│  (UI only)        │ ◀───────────────── │   (all processing)    │ ◀───── │ Catalog API (live)   │
└──────────────────┘                     └──────────────────────┘        └─────────────────────┘
        │                                          │
        ▼                                          ▼
  SQLite (lookup history)              WeasyPrint / python-docx
                                        (PDF / Word generation)
                                                    │
                                                    ▼
                                          OpenAI (insights, optional —
                                          rule-based fallback otherwise)
```

- **`backend/`** (FastAPI) — owns all CMS API integration, field mapping,
  AI insight generation, and document rendering. Stateless, no UI concerns.
- **`frontend/`** (Django) — owns the multi-step UI flow (lookup → manual
  inputs → results), session state, and the history/comparison persistence
  layer. Talks to the backend purely over HTTP — no CMS or PDF logic lives
  here.

Each service has its own virtualenv, its own `requirements.txt`, and its own
`Dockerfile`; `docker-compose.yml` runs both together.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | FastAPI + Pydantic | async I/O for concurrent CMS API calls, schema validation for free |
| Frontend framework | Django | batteries-included session handling + ORM for the history feature, server-rendered (no SPA build step needed for this scope) |
| HTTP client | `httpx` (async) | concurrent fetch of provider-info + claims-measures + state-averages datasets |
| PDF generation | WeasyPrint + Jinja2 | HTML/CSS → print-ready PDF, single template shared mental model with the web UI |
| Word export | `python-docx` | editable `.docx` output as required by the bonus spec |
| Charts | Chart.js | lightweight, CDN-loaded, no frontend build pipeline |
| AI insights / Sanavox chat | OpenAI API, `gpt-4o-mini` | narrative summaries + grounded Q&A, both with safe fallbacks if unavailable |
| Persistence | SQLite via Django ORM | minimal footprint for the history/comparison extra — not used anywhere in the core MVP, which is otherwise stateless |
| Containerization | Docker + Docker Compose | both services build and run identically locally and in deployment |
| CI | GitHub Actions | both test suites run on every push/PR |
| Deployment | Render (Blueprint) | free-tier, Docker-based, one `render.yaml` covers both services |

## Data mapping

| Report field | Source | Notes |
|---|---|---|
| Name of Facility | CMS API, optional manual override | override replaces the displayed name only — never the brand header |
| Location | CMS API | full address |
| EMR, Current Census, Type of Patient, Medelite history fields | Manual input | not available in any public CMS dataset |
| Census Capacity | CMS API | "Number of Certified Beds" |
| Overall / Health Inspection / Staffing / Quality of Resident Care | CMS API | 1–5 star ratings, Provider Info dataset |
| 12-line Hospitalization/ED table | CMS API | short-stay (STR) + long-stay (LT) claims-based measures, each with facility value + national avg + state avg |

## Running it locally

**Backend:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt   # first run only
uvicorn app.main:app --reload --port 8001
```

**Frontend** (second terminal):
```bash
cd frontend
source venv/bin/activate
pip install -r requirements.txt   # first run only
python manage.py migrate          # first run only
python manage.py runserver 8000
```

Visit `http://localhost:8000`, enter CCN `686123` to try the validated test
case. To enable AI-generated insights and the Sanavox chat (optional — both
fall back gracefully without it), create `backend/.env`:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**Or with Docker:**
```bash
docker compose up --build
```

## Tests

```bash
cd backend  && source venv/bin/activate && python -m pytest
cd frontend && source venv/bin/activate && python manage.py test assessment
```
16 tests total (8 backend, 8 frontend), run automatically in CI on every
push/PR via `.github/workflows/ci.yml`. Backend tests run against frozen CMS
fixtures — no network access needed.

## Deployment

Live on **Render's free tier**, deployed as a single **Blueprint**
(`render.yaml` at the repo root) covering both services in one apply:

- **`medelite-frontend`** — Django, built from `frontend/Dockerfile`. This is
  the URL shared with evaluators above.
- **`medelite-backend`** — FastAPI, built from `backend/Dockerfile`. Not
  meant to be visited directly — the frontend talks to it over
  `BACKEND_API_URL`, and it must stay running for any CCN lookup to work.

Both came up together from the one Blueprint apply, so there's nothing
extra to deploy or wire up separately.

**How it connects to GitHub:** Render's GitHub App is authorized against
this repository (`RAJARANJITH1999/MedeLite_Assesment_Raja_Asileti`). Render
reads `render.yaml`, provisions both web services from their respective
Dockerfiles, and — because the GitHub connection is live, not a one-time
upload — every subsequent push to `main` triggers an automatic rebuild and
redeploy of both services. No manual re-upload step.

**Secrets never touch the repo:** `OPENAI_API_KEY` is declared in
`render.yaml` with `sync: false`, which tells Render "don't expect this from
a file — prompt for it once in the dashboard and store it server-side."
`DJANGO_SECRET_KEY` uses `generateValue: true`, so Render generates a random
secret itself at first deploy. Both are pasted directly into Render's
Environment Variables UI for the relevant service, never committed.

**Free-tier caveats** (worth knowing before evaluating it):
- Both services **spin down after 15 minutes of inactivity** and take
  roughly 30–60 seconds to wake up on the next request — if the first load
  feels slow, that's a cold start, not a bug.
- The free plan has **no persistent disk**, so the SQLite-backed lookup
  history resets on every redeploy/restart. Fine for evaluating the core
  report-generation flow; not meant to demonstrate durable history storage
  on this tier.

## Notable engineering decisions

- **Shared field order/labels module** (`backend/app/services/report_fields.py`)
  — both the PDF and the `.docx` exporter read from one source of truth for
  the 24-row report layout, so the two formats structurally cannot drift
  apart from each other.
- **Branding guardrail enforced by tests, not convention** — both services
  have a dedicated test asserting the "INFINITE" header text survives even
  when a facility-name override is supplied, since this was called out as a
  hard constraint in the brief.
- **AI features degrade, never fail** — both the narrative insights and the
  Sanavox chat assistant check for a configured API key up front and return
  a clean fallback response instead of raising, so a missing/invalid key
  never breaks the core report-generation flow.
- **Async, concurrent CMS fetching** — the three CMS datasets needed per
  facility (provider info, claims measures, state/national averages) are
  fetched concurrently with `httpx`/`asyncio.gather`, not sequentially.

## A note on how this was built

This entire project — requirements analysis, architecture decisions, live
verification of the actual CMS API (rather than assuming field names from
memory), backend, frontend, styling, AI integration, Docker, CI, and tests —
was built in **under 1 hour** working directly with **Claude Code** as an AI
pair-engineer.

That speed wasn't "let the AI write it and hope" — it came from directing
the agent the way you'd direct a capable engineer on a real ticket:
resolving the architecture decision up front (decoupled FastAPI/Django
rather than a framework mashup), insisting on live verification against the
real CMS API instead of trusting stale assumptions, defining the hard
constraints explicitly (branding guardrail) so they got enforced with tests
rather than left to chance, and scoping the "beyond MVP" work (AI insights,
history, Sanavox) deliberately rather than letting it sprawl. The result is
a codebase that's organized, tested, and Dockerized the same way a small
production service would be — not a one-shot demo.
