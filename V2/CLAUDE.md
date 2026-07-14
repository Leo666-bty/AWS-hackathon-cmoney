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

Monorepo scaffolded by the team (`feat(v2): initialize React FastAPI AI
workspace`). Present: `apps/{web,api,ai-training}`, `packages/mindfolio-core`,
Makefile, pnpm workspace, a FastAPI skeleton (`/api/v2/health`), and the built
market catalog. Backend feature work is in progress — see
`V2/docs/api/001-market-data-foundation/` (data foundation + read endpoints).

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

The FastAPI OpenAPI schema is the frozen integration surface — the frontend
generates its typed client from it, so any endpoint/field change is made in the
schema and communicated first. Target v2 endpoints (docs/09):

- `GET /api/v2/stocks/popular` · `GET /api/v2/stocks/search`
- `GET /api/v2/stocks/{id}/months/{yyyy_mm}/envelope`
- `POST /api/v2/reconstructions/validate` · `POST /api/v2/reconstructions/complete`
- `POST /api/v2/confirmed-holdings` · `GET /api/v2/health`

## Engine boundaries (hard rules)

- **Server-authoritative & deterministic**: every number (price validity,
  adjustment factor, return, fingerprint, persona code, confidence, score) is
  computed in the backend. The frontend decides none of them. Same input →
  same result (property tests).
- **Re-validate on complete**: `reconstructions/complete` re-validates all five
  trades from raw input and never trusts a prior `validate` response;
  `confirmed-holdings` re-verifies the candidate belongs to the session.
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
  (300 stocks, ~3584 month envelopes, asOf 2025-12-31). MVP has **no DB** — the
  backend reads this file via `MINDFOLIO_MARKET_DATA_PATH`.
- Pinned constants (from `V2/data/README.md`, already in the build tool): band
  representative price = **1/6 (低) · 1/2 (中) · 5/6 (高)** of the month's raw
  range; corporate action = intra-month adjustment-factor change **> 5%** →
  split raw-price regimes, `corporateAction=true`, band mode refused for that
  month (exact price only). `adjustment_factor = 月末還原收盤 / 月末原始收盤`.
- Persona axis thresholds, `normalized_return` range, and decision-score buckets
  are still qualitative in the docs — feature specs MUST pin them before use
  (they are defects until pinned; Constitution).
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
