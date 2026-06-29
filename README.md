# DPB — Demand Planner Backend

FastAPI + PostgreSQL + Redis backend for the Agentic Demand Planning Platform.
Serves the TanStack Start frontend and orchestrates the Demand Forecasting ADK
(separate repo `demand_forecasting_adk`, via its `adk_service/` HTTP wrapper).

## Architecture
```
frontend ──JWT──> backend (FastAPI) ──X-ADK-Secret──> adk-service (ADK + Gemini)
                       │                                    │
                       └────────── PostgreSQL ──────────────┘
                       └────────── Redis (cache, jobs, blacklist)
```
Postgres-only storage (no S3). Multi-tenancy enforced in the service layer by
`company_id` from the JWT. Session-based forecasting: one `session_id` links
`forecast_sessions`, `modeling_data`, `forecasts`, and `agent_traces`.

## Quick start
```bash
cp .env.example .env                  # GOOGLE_API_KEY can stay as placeholder for now
docker compose up --build             # backend :8000, postgres, redis, mailhog :8025
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed     # admin@demo.com / admin123
```
- API docs: http://localhost:8000/docs   ·   Health: http://localhost:8000/health
- OpenAPI spec for the frontend client: `openapi.json` (repo root)

## Local dev (no Docker)
```bash
cd backend && pip install -e .
export DATABASE_URL=postgresql+asyncpg://dpb:dpb_pass@localhost:5432/dpb
alembic upgrade head && python -m app.seed
uvicorn app.main:app --reload
celery -A app.tasks.celery_app worker --loglevel=info   # separate shell
```

## API surface (`/api/v1`)
- **auth**: login, logout, refresh, signup, me
- **users** (admin): list, create, patch, status
- **import**: sources (GET/POST), sources/{id}/mapping (PUT), sources/{id}/import (POST), lookup (POST)
- **dashboard**: kpis (Redis-cached 5m), filters
- **forecasts**: generate, sessions, sessions/{id}, sessions/{id}/status, sessions/{id}/publish, GET /forecasts
- **overrides**: create (auto ≤10%), approve, reject  (tiers: ≤10 auto, ≤25 planner, >25 admin)
- **agents**: metrics, traces, agents/chat, agents/diagnose

## Forecast flow
`POST /forecasts/generate` → creates a draft `forecast_sessions` row, enqueues a Celery
task, returns `session_id` → task calls `adk-service /run` (X-ADK-Secret) → ADK runs,
persists results by `session_id`, updates Redis status → frontend polls
`/forecasts/sessions/{id}/status`, then reads `/forecasts?session_id=`.

## ADK wiring
The ADK lives in `../demand_forecasting_adk` with an added `adk_service/` wrapper.
Uncomment the `adk-service` block in `docker-compose.yml` and point its build
`context` at that repo. Until a real `GOOGLE_API_KEY` is set, the wrapper runs a
deterministic baseline so the pipeline works end-to-end; set the key to switch to
the real Gemini agents (which choose XGBoost vs Chronos-2). CPU-only.

## Frontend cutover (next)
The frontend is still Supabase-coupled. Replace its `integrations/supabase/*` with an
API client (Bearer + refresh) against this backend: `/auth/*` for auth, `/users` for
the admin page, `/forecasts` + `session_id` for the forecast agent page, `/kpis` +
`/filters` for dashboards. `openapi.json` can generate a typed client.

## Tests
```bash
cd backend && python -m pytest -q     # unit (security, tiers) + app/route import checks
```
