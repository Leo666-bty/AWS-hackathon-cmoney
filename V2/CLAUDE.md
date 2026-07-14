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

The acquisition vertical slice is implemented end to end. `apps/web` contains
the React landing, five-stock builder, per-stock reconstruction wizard, result,
share-card and explicit-consent UI. `apps/api` exposes all eight `/api/v2`
operations; `packages/mindfolio-core` owns deterministic validation,
reconstruction, persona and scoring. Market data is the built file catalog and
confirmed holdings persist in PostgreSQL. `docker-compose.yml` runs web, API
and PostgreSQL together on one EC2. `apps/ai-training` remains an untrained
offline scaffold, and the UI still uses demo identity `LEO`.

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
endpoints (docs/09):

- `GET /api/v2/stocks/popular` · `GET /api/v2/stocks/search`
- `GET /api/v2/stocks/{id}/months/{yyyy_mm}/envelope`
- `POST /api/v2/reconstructions/validate` · `POST /api/v2/reconstructions/complete`
- `POST /api/v2/confirmed-holdings`
- `GET /api/v2/users/{user_id}/confirmed-holdings` · `GET /api/v2/health`

## Engine boundaries (hard rules)

- **Server-authoritative & deterministic**: every number (price validity,
  adjustment factor, return, fingerprint, persona code, confidence, score) is
  computed in the backend. The frontend decides none of them. Same input →
  same result (deterministic regression coverage; broader property-based
  coverage remains a hardening item).
- **Re-validate on complete**: `reconstructions/complete` re-validates all five
  trades from raw input and never trusts a prior `validate` response;
  `confirmed-holdings` statelessly re-runs those five trades and derives only
  `holding_candidates`. Durable reconstruction/session binding is not yet
  implemented and remains an identity-hardening gap.
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
