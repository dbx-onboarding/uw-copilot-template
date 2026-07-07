# UW CoPilot — Web App (FastAPI + React)

A production-grade replacement for the Streamlit workbench. Same Databricks Apps
deployment, same `uw_copilot` backend logic — a real frontend instead of CSS hacks
over Streamlit.

## Why this exists

The Streamlit app relied on brittle CSS targeting Streamlit's internal DOM,
invisible overlay buttons for row clicks, an incoherent color system, and ~40%
placeholder tabs. This version fixes all of that:

- **Real React UI** with a single coherent design system (`src/theme.css`) —
  one dark palette, one brand accent, semantic colors only where they mean risk.
- **The empty tabs are now real**: Claims, Loss Runs, Drivers, and Documents load
  from the operational Delta tables.
- **Identity is server-side**: the signed-in user and RBAC role come from
  Databricks Apps forwarded headers, not a hardcoded name / client-set role.
- **Feedback is written with the correct schema** (rating as INT, `question`/
  `answer`/`created_at`, `session_id` populated) — sidesteps the bugs in
  `uw_copilot.feedback`.
- **Graceful demo mode**: with no SQL warehouse configured it renders on demo
  data, so it runs anywhere (including local dev with no Databricks connection).

## Architecture

```
webapp/
├── app.yaml                # Databricks Apps manifest (uvicorn)
├── requirements.txt
├── server/
│   ├── main.py             # FastAPI routes + identity + static mount
│   └── data.py             # Data access (SQL Warehouse / VS / Serving) + demo fallbacks
└── frontend/
    ├── src/                # React source (Vite)
    └── dist/               # Built static assets (served by FastAPI at /)
```

The FastAPI backend exposes `/api/*` JSON and serves the compiled React app at `/`.

## Local development

```bash
# 1. Backend (terminal 1)
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000

# 2. Frontend dev server with hot reload (terminal 2) — proxies /api to :8000
cd frontend
npm install
npm run dev            # http://localhost:5173
```

## Build + deploy to Databricks Apps

```bash
# Build the frontend (produces frontend/dist)
npm --prefix frontend install && npm --prefix frontend run build

# Deploy. For LIVE data, deploy from the REPO ROOT so ../src, ../config and
# ../prompts ship alongside webapp/ (the backend locates them relative to webapp/).
databricks apps deploy uw-copilot-web --source-code-path /Workspace/Users/<you>/uw-copilot-template
```

Point the app's entry at `webapp/app.yaml`. Rebuild the frontend whenever you
change anything under `frontend/src`.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/me` | Current user + role + live/demo flag |
| GET | `/api/submissions` | Queue + KPIs |
| GET | `/api/submissions/{id}` | Detail + AI assessment |
| GET | `/api/submissions/{id}/{claims\|loss_runs\|drivers\|documents\|similar}` | Sub-tables |
| POST | `/api/chat` | Proxy to the RAG serving endpoint |
| POST | `/api/feedback` | Thumbs up/down |
| POST | `/api/decisions` | Approve / Refer / Decline / Request Info |
```
