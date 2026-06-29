# Review Changelog — 2026-06-29

Backend (`DPB/backend`) + ADK wrapper (`demand_forecasting_adk/adk_service`) review pass.
API contract (29 routes) and DB schema (12 tables) preserved. ADK core
(`demand_forecasting_agent/`) untouched.

## Applied (low-risk, high-value)

| # | Sev | File | Change | Why |
|---|-----|------|--------|-----|
| B1 | Blocker | `backend/pyproject.toml` | Pin `bcrypt>=4.0,<4.1` | passlib 1.7.4 + bcrypt ≥4.1/5.x breaks ALL password hashing (`ValueError: >72 bytes` on any password) → login/signup/user-create 500. Fresh install resolved bcrypt 5.0.0. Verified: failing test now passes. |
| H1 | High | `backend/app/tasks/forecast_tasks.py` | Dispose async `engine` + close `redis_client` in `finally` | Celery runs each task in a fresh `asyncio.run()` loop; the module-level async engine/redis bind connections to the creating loop, so the 2nd task per worker hit "Future attached to a different loop". Safe under prefork (one task/process). |
| H2 | High | `adk_service/db.py` | `CAST(:cid AS uuid)` on `company_id` (reads+writes); `CAST(:d AS date)` on string dates | psycopg3 sends `str` params as `text`; PostgreSQL has no `uuid = text` operator and won't assign `text`→`uuid`/`date`, so the ADK persist/read path would fail at runtime. Casts are no-ops for valid values. |
| M1 | Med | `backend/app/main.py` | Add `SlowAPIMiddleware` | `default_limits` (100/min) were configured but never enforced — slowapi needs the middleware for global limits. |
| L1 | Low | `backend/app/services/metrics_service.py` | Remove unused `abs_err` accumulator | Dead; duplicated `wabs`, never used in output. |
| L4 | Low | `adk_service/main.py` | Remove dead `has_real_gemini_key` import | Unused (`runner.has_real_gemini_key` is the one used). |

## Verified
- `python -m compileall -q app` → OK
- `python -m pytest -q` → **4 passed** (was 3 passed / 1 failed pre-fix)
- `len(app.openapi()['paths'])` → **29**
- `len(Base.metadata.tables)` → **12**
- `python -m py_compile adk_service/*.py` → OK
- `openapi.json` NOT re-exported (no route changes).

## Dependency note
- Added explicit `bcrypt>=4.0,<4.1` pin (B1). No genuinely new packages — bcrypt was already
  an implicit extra of `passlib[bcrypt]`; it's now pinned to a working range.

## Applied — round 2 (approved follow-ups)

| # | Sev | File | Change | Why |
|---|-----|------|--------|-----|
| H3 | High | `adk_service/runner.py` | Serialize ADK runs under a process lock; select only the `*forecasts_*.csv` produced *during* the locked run (snapshot before, diff after) | The ADK resolves its artifacts dir once at import and writes shared, timestamp-named (not session-scoped) CSVs/pickles. Picking the globally-newest CSV could return another tenant's forecast under concurrency, and concurrent runs corrupt each other's intermediates. The lock guards a single adk-service process (the documented deployment); horizontal scaling would need a distributed lock — noted in code. ADK core untouched. |
| M2 | Med | `auth_service.py`, `api/v1/auth.py`, `schemas/auth.py` | `refresh()` now rejects blacklisted refresh tokens and revokes (rotates) the consumed jti; `logout` accepts an optional `refresh_token` and blacklists it too | Previously logout left the refresh token valid for 7d and refresh tokens were replayable / never rotated. **Contract change (called out):** `POST /auth/logout` gains an optional `LogoutIn` body (`refresh_token?`). Backward compatible — logout with no body still revokes the access token. Note: concurrent double-refresh now fails the 2nd call (standard rotation semantics). |

### openapi.json re-export (H3/M2)
Re-exported `backend/openapi.json` (and synced the identical root mirror `DPB/openapi.json`).
**Paths still 29** — the only diff is the new `LogoutIn` schema and the optional request body +
422 response on `/auth/logout`. No other endpoint changed.

## Proposed — NOT applied (need go-ahead; larger / contract / behavior-affecting)

- **M3 (Med) — `modeling_data` not persisted on real ADK runs** (`runner.py:120`, `modeling=[]`).
  Before/after UI comparison will be empty for Gemini runs.
- **M4 (Med) — CORS `allow_origins=["*"]` + `allow_credentials=True`** (`main.py`). Unnecessary
  with Bearer auth; weakens posture. Deployment-config decision.
- **L2 (Low)** — override with `original_value == 0` auto-approves any magnitude (`override_service.py:43`).
- **L3 (Low)** — `runner.py:121` `fdf.shape[0] and len({...})` short-circuit is confusing.
- **L5 (Low)** — KPI cache has no invalidation on new upload; relies on 5-min TTL.
