# CLAUDE.md — Mindfolio V2

Guidance for Claude Code when working under `V2/`. **V2 is the active version.**
`V1/` is archived (Reverse Portfolio Onboarding) and out of scope — do not edit
it. The authoritative engineering rules are `V2/.specify/memory/constitution.md`;
this file is the fast orientation.

## What this is

Mindfolio Time Machine V2 — "2025 投資時光機 × 投資人格實驗室". A user picks five
familiar stocks from a 300-stock catalog, gives each a buy month + price
(band or exact) and a still-holding/sold state; the **Portfolio Reconstruction
Engine** validates prices, adjusts for corporate actions, rebuilds returns, and
produces a Portfolio Fingerprint, a four-axis persona, a data-confidence score,
and a shareable result. Only "still holding" + consent becomes a confirmed
holding. The engine (deterministic Python), not the JS demo, is the technical
moat.

Product source of truth: `V2/docs/00_PROJECT_CHARTER.md`; computation/persona:
`02_QUIZ_PERSONALITY_AND_SCORING.md`; data claims: `03_DATA_AND_GUARDRAILS.md`;
architecture: `08`/`09`.

## Current state

The two-stage lifecycle — **Time Machine (acquisition) → Portfolio Radar
(retention)** — is implemented end to end. `apps/web` contains the React
landing, five-stock builder, per-stock reconstruction wizard, result,
share-card and explicit-consent UI, plus `/activate` (invite-code activation)
and `/app` (Portfolio Radar dashboard, incl. a structured AI Deep Dive).
`apps/api` exposes 14 `/api/v2` operations (6 acquisition + 6 retention + 2 AI,
retention and AI both in `routers/retention.py`); `packages/mindfolio-core` owns
deterministic validation, reconstruction, persona and scoring. Market data is the
built file catalog; confirmed holdings plus `reconstruction_reports` (incl. the
AI-report cache), `action_card_feedback` and `interaction_events` persist in
PostgreSQL. `docker-compose.yml` runs web, API and PostgreSQL together on one EC2.
`apps/ai-training` is a completed offline pipeline: it scores the official 2025
CSVs into a versioned, checksummed pre-scored artifact (`market-context-2025-v1.json`,
3,584 stock-month contexts); the API reads that JSON O(1) and never installs or
loads sklearn/joblib. Identity is server-derived: an invite-code adapter issues a
session token (on-site `Neal` / `Leo` via `invite_identities="123456:Neal,000000:Leo"`); the retention
surface never trusts a client-supplied `user_id`. Real Bedrock is verified
working live on EC2 (Converse, `openai.gpt-oss-120b-1:0`, authed with a
short-term Bedrock API key / bearer token because the workshop account blocks
IAM roles); the repo default stays `bedrock_enabled=false` (enabled via env var
on deploy) and any failure still falls back deterministically. Not yet done:
the action-card `mute` preference is stored but not yet acted on
(Moment-Engine ranking deferred to Feature 006); `docs/api/004..007` per-feature
SDD folders are not yet written. Python suite: 77 tests (web: 6).

## Toolchain & commands (NOT uv)

Python is venv + pip + `V2/python-requirements.txt` (editable per-app
`pyproject.toml`), driven by the Makefile. Frontend is pnpm.

```bash
cd V2
make install                 # pnpm install + venv + pip install requirements
make dev-api                 # uvicorn mindfolio_api.main:app --reload :8000
make dev-web                 # vite (React) :5173
make test                    # pnpm test:web + pytest across core/api/ai-training
make build
```

- API base path: **`/api/v2`** (health `/api/v2/health`, docs `/api/v2/docs`,
  schema `/api/v2/openapi.json`). Settings prefix `MINDFOLIO_`.
- Rebuild catalog: `python3 V2/tools/build_market_catalog.py --json`.

## Architecture

```text
React + TS (apps/web)  →  FastAPI (apps/api, /api/v2)
                            routers → services → repositories → ai/
                            └─ calls packages/mindfolio-core (pure calc + DTOs)
data: file catalog (V2/data/market-catalog.json), MINDFOLIO_MARKET_DATA_PATH
```

**Code placement (hard rule)**: pure deterministic calculation + domain models
(envelope validation, corporate-action adjustment, return, fingerprint,
persona, score) live in `packages/mindfolio-core` (pydantic only, no FastAPI,
shared with `ai-training` to avoid training-serving skew). HTTP
routers/schemas/services/repositories + Bedrock orchestration live in
`apps/api`; they call core.

## API contract is law

The FastAPI OpenAPI schema is the frozen integration surface. The current
frontend uses a hand-written TypeScript + Zod client; OpenAPI codegen and a
generated-client contract test remain production hardening. Any endpoint/field
change is still made in the schema and communicated first. Implemented v2
endpoints (14 total, docs/09):

Acquisition (6):
- `GET /api/v2/health`
- `GET /api/v2/stocks/popular` · `GET /api/v2/stocks/search`
- `GET /api/v2/stocks/{id}/months/{yyyy_mm}/envelope`
- `POST /api/v2/reconstructions/validate` · `POST /api/v2/reconstructions/complete`
  (complete also returns a `report` handle: `{report_id, claim_token, expires_at}`)

Retention (6, `routers/retention.py`, session-authenticated):
- `POST /api/v2/auth/session` (invite code → session token; identity server-derived)
- `POST /api/v2/reports/{report_id}/claim`
- `POST /api/v2/reports/{report_id}/confirmed-holdings` (the only confirmed-holdings write path)
- `GET /api/v2/me/dashboard`
- `POST /api/v2/me/action-cards/{card_id}/feedback`
- `POST /api/v2/events/batch`

AI Deep Dive (2, `routers/retention.py`, session-authenticated, report-owner-only):
- `POST /api/v2/reports/{report_id}/ai-report` (structured `InvestmentAIReport`;
  PostgreSQL-cached by `context|model|content_sha256|prompt` (artifact checksum
  in the key so a re-trained artifact invalidates); Bedrock schema-validated +
  guardrailed, any failure → deterministic fallback, `source` flags which)
- `POST /api/v2/reports/{report_id}/questions` (only 3 server-defined question IDs:
  `why-persona`, `most-influential-trade`, `why-anomalous-month`; no free chat)

**Removed for security**: the old unauthenticated `POST /api/v2/confirmed-holdings`
and `GET /api/v2/users/{user_id}/confirmed-holdings` (trusted a client `user_id`, a
cross-member isolation hole) no longer exist — use the report-scoped path above.

## Engine boundaries (hard rules)

- **Server-authoritative & deterministic**: every number (price validity,
  adjustment factor, return, fingerprint, persona code, confidence, score) is
  computed in the backend. The frontend decides none of them. Same input →
  same result (deterministic regression coverage; broader property-based
  coverage remains a hardening item).
- **Re-validate on complete**: `reconstructions/complete` re-validates all five
  trades from raw input and never trusts a prior `validate` response, and (when
  the store is available) emits a `report` handle. Confirmed holdings are now
  written only via the session-authenticated, report-scoped
  `POST /reports/{report_id}/confirmed-holdings`, which statelessly re-runs the
  claimed report's trades, derives `holding_candidates`, and records
  `source_report_id`. Durable reconstruction/session binding is therefore now in
  place (invite-code session + report claim + `source_report_id`); a real
  end-user login/registration flow beyond the invite-code adapter remains an
  identity-hardening item.
- **AI only narrates verified results**: Bedrock receives a verified DTO
  (never raw prices, credentials, full event history, or PII), its output is
  Pydantic-validated, and on any failure a deterministic fixed-template
  narrative is used. AI never recomputes a number or overwrites a persona code.
  No buy/sell direction, target price, return guarantee, or psychological
  diagnosis — the persona is a shareable product label, not a psych scale.
- **Confirmed-holding gate**: `quiz_stock_interest`, `reconstructed_trade`, and
  `confirmed_holding` are distinct; only explicit "still holding" + consent
  writes a confirmed holding. Reconstructions are memory-based estimates, not
  broker proof.

## Data facts

- Catalog built from the organizer CSVs in `V2/data/Delivery_…/`
  (raw data lives under the active version; gitignored) by
  `V2/tools/build_market_catalog.py` → `V2/data/market-catalog.json`
  (300 stocks, 3584 month envelopes, asOf 2025-12-31). Read-only market data
  stays file-based via `MINDFOLIO_MARKET_DATA_PATH`; PostgreSQL stores only
  user-confirmed holdings selected through the consent gate.
- Pinned constants (from `V2/data/README.md`, already in the build tool): band
  representative price = **1/6 (低) · 1/2 (中) · 5/6 (高)** of the month's raw
  range; corporate action = intra-month adjustment-factor change **> 5%** →
  split raw-price regimes, `corporateAction=true`, band mode refused for that
  month (exact price only). `adjustment_factor = 月末還原收盤 / 月末原始收盤`.
- Persona thresholds, `normalized_return`, confidence and decision-score
  formulas are pinned in `docs/02_QUIZ_PERSONALITY_AND_SCORING.md` and
  `docs/api/002-reconstruction-engine/spec.md`, then implemented in
  `packages/mindfolio-core`.
- Note: `V2/demo/market-data.js` (full 300-stock price snapshot) is committed by
  the team; confirm redistribution licensing before making the repo public.

## Spec-driven development

Spec Kit under `V2/.specify` (+ `V2/.claude/skills`). Flow: specify → clarify →
plan → tasks → analyze → implement. Feature specs live in
`V2/docs/api/<###-feature>/`; `V2/.specify/feature.json` points at the active
one. Constitution: `V2/.specify/memory/constitution.md`.

## Degradation

The core loop (five-stock reconstruction → result → persona/score) must complete
with the AI provider down (deterministic fallback narrative). Fail fast at
startup on a missing catalog; runtime failures are recoverable errors, never a
silent frontend-computed fake result.
