<!--
Sync Impact Report
- Version change: (template) → 1.0.0 (V2 ratification; derived from V1 constitution 1.1.0)
- Product pivot: V1 "Reverse Portfolio Onboarding" → V2 "2025 投資時光機 ×
  投資人格實驗室" (Portfolio Reconstruction Engine). Principles re-authored for
  the reconstruction/persona domain; V1's engineering discipline carries over.
- Principles (6): I Contract-First · II Server-Authoritative Deterministic
  Engine · III AI Narrative Guardrails · IV Test-First · V Confirmed-Holding
  Gate & Data Honesty · VI Demo-Complete Degradation
- Templates: plan/spec/tasks templates compatible as-is (generic gates)
- Follow-up: feature specs must PIN the currently-undefined constants
  (persona axis thresholds, band representative price, normalization ranges,
  decision-score buckets) — see Technical Constraints.
-->

# Mindfolio V2 Constitution

Applies to all work under `V2/`. V1 (`V1/`) is archived and out of scope.

## Core Principles

### I. Contract-First API (NON-NEGOTIABLE)

The FastAPI OpenAPI schema is the single authoritative contract between the
React frontend and the backend; the frontend generates its typed client from
it. The API MUST expose exactly the endpoints, field names, enum values, and
base path defined there. Any contract change is made in the schema first and
communicated before either side writes code against it.

Rationale: frontend and backend are built in parallel by two people; the
OpenAPI contract is the only integration surface, so it must not drift.

### II. Server-Authoritative Deterministic Engine (NON-NEGOTIABLE)

Every number the product shows — price-envelope validity, corporate-action
adjustment factor, reconstructed return, portfolio-fingerprint vector, persona
code, reconstruction confidence, decision score — MUST be computed by
deterministic Python in the backend. The frontend MUST NOT decide any of them.
`reconstructions/complete` MUST re-validate all five trades from raw input and
MUST NOT trust any prior `validate` response. Identical input MUST always
produce identical result (reproducible; locked by property tests). The LLM
never performs arithmetic and never overwrites a persona code.

Rationale: the frontend is a UX layer, not a trust boundary; the reconstruction
engine — not the JavaScript demo — is the technical moat, and a judge must be
able to recompute any figure.

### III. AI Narrative Guardrails

The AI service receives only a verified result DTO — never raw/unvalidated
prices, database credentials, full anonymous event history, or identifiable
personal data. Its output MUST pass a Pydantic schema before use; on timeout,
schema failure, or provider error, a deterministic fixed-template narrative is
substituted and the core result still returns. Generated content MUST never
contain buy/sell direction, target prices, or return guarantees, MUST NOT
reframe the persona as a psychological diagnosis, and MUST NOT recompute or
contradict any deterministic number.

Rationale: financial + personality context; one hallucinated recommendation or
"diagnosis" invalidates the product's honesty claim.

### IV. Test-First

TDD is mandatory for backend code: failing test → minimal implementation →
refactor. Target 80%+ coverage. Beyond units, the engine REQUIRES property
tests: a sell month is never earlier than its buy month; a price outside the
month envelope is always rejected; a price across a corporate-action regime
boundary is rejected; the same input yields the same persona and score.
Contract tests validate every endpoint against the OpenAPI schema.

Rationale: the engine's correctness lives in edges (regime splits, boundary
prices, month alignment); those must be caught mechanically.

### V. Confirmed-Holding Gate & Data Honesty

Three data types are distinct and never conflated: `quiz_stock_interest`,
`reconstructed_trade`, and `confirmed_holding`. A `confirmed_holding` is
written ONLY when the user explicitly marks a stock "still holding" AND
consents; the backend re-verifies the candidate belongs to that
reconstruction/session before writing. Reconstructions are estimates from user
memory, not broker proof — the product MUST say so; price-plausibility checks
only catch obvious garbage, they do not prove a trade happened. Anonymous
sessions and member profiles use different identifiers and tables.

Rationale: the product's credibility rests on never dressing a quiz answer or a
guessed price up as verified holdings.

### VI. Demo-Complete Degradation

The core loop (five-stock reconstruction → result → persona/score) MUST
complete under every degradation: AI provider down (deterministic fallback
narrative), and the result still returns. The service fails fast at startup on
missing market data; runtime failures are graceful (recoverable error, never a
frontend-computed fake result — a failed API call shows an error, it does not
silently degrade into an unverified browser calculation).

Rationale: a hackathon demo gets one shot; every dependency may fail except the
reconstruction result itself.

## Technical Constraints & Scope

- Stack (as built by the team, 2026-07-14): React + TypeScript frontend
  (pnpm workspace), FastAPI + Python backend, Amazon Bedrock (backend IAM only).
  Monorepo: `V2/apps/{web,api,ai-training}` + shared `V2/packages/mindfolio-core`
  (deterministic domain logic + model contracts shared by API and training to
  avoid training-serving skew). Python is managed by **venv + pip +
  `V2/python-requirements.txt`** (editable per-app `pyproject.toml`), driven by
  the **Makefile** (`make install|dev-api|dev-web|test|build`) — not uv. API
  base path is **`/api/v2`**; settings use the `MINDFOLIO_` env prefix.
- Code placement: pure deterministic calculation and domain models
  (envelope validation, adjustment, return, fingerprint, persona, score) live
  in `packages/mindfolio-core`; HTTP routers/schemas/services/repositories and
  Bedrock orchestration live in `apps/api` and call core. AI code in
  `apps/api/ai/`.
- Data: a 300-stock 2025 market catalog is built from the three organizer CSVs
  by `V2/tools/build_market_catalog.py` into a structured catalog file
  (per-stock, per-month raw low/high, month-end raw & adjusted close, adjustment
  factor, corporate-action flag). The backend reads it via
  `MINDFOLIO_MARKET_DATA_PATH` — market data stays file-based (read-only).
  User state (confirmed holdings) is persisted in PostgreSQL self-hosted on the
  same EC2 instance as the API (not RDS) via `DATABASE_URL`; a DB outage yields
  HTTP 503 at request time and never crashes startup or blocks the reconstruction
  loop. Raw organizer CSVs/PDFs live in `V2/data/`
  (the active version owns its data) and stay gitignored — never committed; the
  built `V2/data/market-catalog.json` is the shared fixture.
- Corporate action: `factor = adjusted_close / raw_close`;
  `comparable_user_price = raw_user_price × factor`; if intra-month factor
  varies > 5%, flag `corporateAction=true`, split raw-price regimes, and reject
  fuzzy bands that cross a regime.
- **Constants that feature specs MUST pin** (currently qualitative in the docs;
  same discipline as any deterministic number): persona four-axis thresholds
  (L/T, H/A, D/C, X/E cutoffs), band-mode representative price
  (偏低/中間/偏高 → which number), `normalized_return` normalization range,
  and decision-score bucket boundaries. Unpinned constants are a defect.
- Training exception (offline only): `V2/apps/ai-training` may train
  UNSUPERVISED market-regime clustering and an anomaly detector over the 2025
  stock-month features. It MUST NOT predict holdings, price direction, or
  buy/sell; persona stays deterministic until enough explicit user labels
  exist. The online API loads approved artifacts for inference only, never
  trains during a request. Model artifacts record feature version, data range,
  metrics, and `generated_at`.
- Out of scope for the 3-day hackathon (docs/07 cut lines): real login, real
  push notifications, image sharing, leaderboards, free-text chat, broker
  integration, multi-batch/partial trades. Never cut: front/back separation,
  FastAPI, 300-stock search, price validation, month reconstruction,
  corporate-action adjustment, the confirmed-holding boundary, the technical
  result page.

## Development Workflow

- Spec-driven development via Spec Kit: specify → clarify → plan → tasks →
  analyze → implement. Feature specs live under `V2/docs/api/<###-feature>/`
  (`V2/.specify/feature.json` points there); decisions that shift product
  consensus propagate back into `V2/docs/00–10`.
- Product-scope source of truth: `V2/docs/00_PROJECT_CHARTER.md` (proposition),
  `02_QUIZ_PERSONALITY_AND_SCORING.md` (computation/persona),
  `03_DATA_AND_GUARDRAILS.md` (data claims), `08`/`09` (engine & architecture).
  If a doc conflicts with the charter on scope, the charter wins and this
  constitution is amended.
- Parallel-dev discipline (monorepo now pushed): the FastAPI OpenAPI schema is
  the frozen integration surface — the frontend generates its typed client from
  it, so any endpoint/field change is made in the schema and communicated first.
  Backend work is scoped to `V2/apps/api/` and `V2/packages/mindfolio-core`;
  shared roots (`V2/python-requirements.txt`, `Makefile`, `pnpm-workspace.yaml`)
  are edited minimally and coordinated with the teammate.
- Conventional commits; code review before merge (CRITICAL/HIGH block).

## Governance

This constitution supersedes ad-hoc practice for all `V2/` work. Amendments
edit this file with a semantic version bump (MAJOR: principle removal/redefine;
MINOR: new principle or materially expanded guidance; PATCH: clarification) and
a note in the Sync Impact Report. Every plan's Constitution Check gate MUST
verify Principles I–VI; violations require a justified entry in the plan's
Complexity Tracking table. Runtime agent guidance (a V2 CLAUDE.md, when added)
must stay consistent with this document.

**Version**: 1.0.0 | **Ratified**: 2026-07-14 | **Last Amended**: 2026-07-14
